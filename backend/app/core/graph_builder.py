import logging
import time
from typing import Dict, List, Any, Optional
from app.core.db import db_manager
from app.core.parser import ParsedFile, SymbolInfo

logger = logging.getLogger("codeimpact.graph_builder")

class GraphBuilder:
    """Builds and indexes repository structure, symbols, and dependencies into FalkorDB."""

    def __init__(self, db=db_manager):
        self.db = db

    def get_graph_name(self, repo_id: str) -> str:
        # Sanitize graph name for FalkorDB
        clean = repo_id.replace("-", "_").replace(".", "_")
        return f"repo_{clean}"

    def build_graph(
        self,
        repo_id: str,
        repo_name: str,
        repo_path: str,
        parsed_files: Dict[str, ParsedFile],
    ) -> Dict[str, Any]:
        """
        Build complete property graph in FalkorDB from parsed files.
        Clears existing graph if re-indexing to ensure idempotency.
        """
        graph_name = self.get_graph_name(repo_id)
        logger.info(f"Indexing repository {repo_id} into FalkorDB graph '{graph_name}'...")
        
        # Reset graph for clean idempotent build
        self.db.clear_graph(graph_name)

        # 1. Create Repository Node
        total_files = len(parsed_files)
        total_symbols = sum(len(pf.symbols) for pf in parsed_files.values())

        repo_query = """
        CREATE (r:Repository {
            id: $repo_id,
            name: $repo_name,
            path: $repo_path,
            indexed_at: $indexed_at,
            total_files: $total_files,
            total_symbols: $total_symbols
        })
        """
        self.db.execute_query(
            graph_name,
            repo_query,
            {
                "repo_id": repo_id,
                "repo_name": repo_name,
                "repo_path": repo_path,
                "indexed_at": time.time(),
                "total_files": total_files,
                "total_symbols": total_symbols,
            },
        )

        # 2. Insert Files
        file_count = 0
        symbol_count = 0
        test_count = 0
        relationship_count = 0

        # Module to File Path lookup
        module_to_file: Dict[str, str] = {
            pf.module_name: pf.file_path for pf in parsed_files.values()
        }

        for rel_path, pf in parsed_files.items():
            file_id = f"{repo_id}:{rel_path}"
            create_file_query = """
            MATCH (r:Repository {id: $repo_id})
            CREATE (f:File {
                id: $file_id,
                repo_id: $repo_id,
                path: $file_path,
                module_name: $module_name,
                total_lines: $total_lines,
                is_test: $is_test,
                language: 'python'
            })
            CREATE (r)-[:CONTAINS]->(f)
            """
            self.db.execute_query(
                graph_name,
                create_file_query,
                {
                    "repo_id": repo_id,
                    "file_id": file_id,
                    "file_path": rel_path,
                    "module_name": pf.module_name,
                    "total_lines": pf.total_lines,
                    "is_test": pf.is_test_file,
                },
            )
            file_count += 1
            relationship_count += 1

            # Insert Symbols and Tests
            for sym in pf.symbols:
                sym_id = f"{repo_id}:{sym.id}"
                
                if sym.is_test:
                    # Test Node
                    create_test_query = """
                    MATCH (f:File {id: $file_id})
                    CREATE (t:Test {
                        id: $sym_id,
                        repo_id: $repo_id,
                        name: $name,
                        qualified_name: $qualified_name,
                        file_path: $file_path,
                        start_line: $start_line,
                        end_line: $end_line,
                        docstring: $docstring,
                        test_type: 'unit'
                    })
                    CREATE (f)-[:CONTAINS]->(t)
                    """
                    self.db.execute_query(
                        graph_name,
                        create_test_query,
                        {
                            "file_id": file_id,
                            "sym_id": sym_id,
                            "repo_id": repo_id,
                            "name": sym.name,
                            "qualified_name": sym.qualified_name,
                            "file_path": sym.file_path,
                            "start_line": sym.start_line,
                            "end_line": sym.end_line,
                            "docstring": sym.docstring or "",
                        },
                    )
                    test_count += 1
                    relationship_count += 1
                else:
                    # Regular Symbol Node
                    create_symbol_query = """
                    MATCH (f:File {id: $file_id})
                    CREATE (s:Symbol {
                        id: $sym_id,
                        repo_id: $repo_id,
                        name: $name,
                        qualified_name: $qualified_name,
                        symbol_type: $symbol_type,
                        file_path: $file_path,
                        start_line: $start_line,
                        end_line: $end_line,
                        docstring: $docstring,
                        parameters: $parameters,
                        language: 'python'
                    })
                    CREATE (f)-[:CONTAINS]->(s)
                    """
                    self.db.execute_query(
                        graph_name,
                        create_symbol_query,
                        {
                            "file_id": file_id,
                            "sym_id": sym_id,
                            "repo_id": repo_id,
                            "name": sym.name,
                            "qualified_name": sym.qualified_name,
                            "symbol_type": sym.symbol_type,
                            "file_path": sym.file_path,
                            "start_line": sym.start_line,
                            "end_line": sym.end_line,
                            "docstring": sym.docstring or "",
                            "parameters": ",".join(sym.parameters),
                        },
                    )
                    symbol_count += 1
                    relationship_count += 1

        # 3. Create File-level IMPORTS and DEPENDS_ON relationships
        for rel_path, pf in parsed_files.items():
            source_file_id = f"{repo_id}:{rel_path}"
            imported_files: set = set()

            for imp in pf.imports:
                target_mod = imp.module
                # check if target module maps to a known file
                if target_mod in module_to_file:
                    imported_rel_path = module_to_file[target_mod]
                    if imported_rel_path != rel_path:
                        imported_files.add(imported_rel_path)
                elif imp.imported_name:
                    combined = f"{target_mod}.{imp.imported_name}"
                    if combined in module_to_file:
                        imported_rel_path = module_to_file[combined]
                        if imported_rel_path != rel_path:
                            imported_files.add(imported_rel_path)

            for target_rel_path in imported_files:
                target_file_id = f"{repo_id}:{target_rel_path}"
                import_edge_query = """
                MATCH (s:File {id: $source_id}), (t:File {id: $target_id})
                CREATE (s)-[:IMPORTS]->(t)
                CREATE (s)-[:DEPENDS_ON]->(t)
                """
                self.db.execute_query(
                    graph_name,
                    import_edge_query,
                    {"source_id": source_file_id, "target_id": target_file_id},
                )
                relationship_count += 2

        # 4. Create CALLS and TESTS relationships between Symbols/Tests
        unresolved_call_count = 0
        resolved_call_count = 0

        for rel_path, pf in parsed_files.items():
            for sym in pf.symbols:
                caller_id = f"{repo_id}:{sym.id}"
                is_caller_test = sym.is_test

                for call in sym.calls:
                    if call.unresolved or not call.resolved_symbol_id:
                        unresolved_call_count += 1
                        continue

                    target_id = f"{repo_id}:{call.resolved_symbol_id}"
                    
                    if is_caller_test:
                        # Test calls/tests Symbol
                        test_edge_query = """
                        MATCH (t:Test {id: $caller_id}), (s:Symbol {id: $target_id})
                        CREATE (t)-[:TESTS {line: $line}]->(s)
                        CREATE (t)-[:CALLS {line: $line}]->(s)
                        """
                        self.db.execute_query(
                            graph_name,
                            test_edge_query,
                            {"caller_id": caller_id, "target_id": target_id, "line": call.line_number},
                        )
                        relationship_count += 2
                        resolved_call_count += 1
                    else:
                        # Symbol calls Symbol
                        calls_edge_query = """
                        MATCH (s1:Symbol {id: $caller_id}), (s2:Symbol {id: $target_id})
                        CREATE (s1)-[:CALLS {line: $line}]->(s2)
                        """
                        self.db.execute_query(
                            graph_name,
                            calls_edge_query,
                            {"caller_id": caller_id, "target_id": target_id, "line": call.line_number},
                        )
                        relationship_count += 1
                        resolved_call_count += 1

        logger.info(
            f"Graph build completed for {repo_id}: {file_count} files, {symbol_count} symbols, "
            f"{test_count} tests, {relationship_count} relationships, "
            f"{resolved_call_count} resolved calls, {unresolved_call_count} unresolved."
        )

        return {
            "graph_name": graph_name,
            "repo_id": repo_id,
            "total_files": file_count,
            "total_symbols": symbol_count,
            "total_tests": test_count,
            "total_relationships": relationship_count,
            "resolved_calls": resolved_call_count,
            "unresolved_calls": unresolved_call_count,
        }

graph_builder = GraphBuilder()
