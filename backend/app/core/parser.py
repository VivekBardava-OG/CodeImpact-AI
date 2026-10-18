import ast
import os
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field

@dataclass
class ImportInfo:
    module: str
    imported_name: Optional[str] = None
    alias: Optional[str] = None
    is_relative: bool = False
    relative_level: int = 0
    line_number: int = 0

@dataclass
class CallInfo:
    callee_name: str
    line_number: int
    is_method: bool = False
    object_name: Optional[str] = None
    resolved_symbol_id: Optional[str] = None
    unresolved: bool = True

@dataclass
class SymbolInfo:
    id: str  # Unique stable id: {file_path}:{name} or {file_path}:{class}.{name}
    name: str
    qualified_name: str
    symbol_type: str  # "function", "class", "method"
    file_path: str
    start_line: int
    end_line: int
    docstring: Optional[str] = None
    parameters: List[str] = field(default_factory=list)
    class_name: Optional[str] = None
    is_test: bool = False
    calls: List[CallInfo] = field(default_factory=list)

@dataclass
class ParsedFile:
    file_path: str
    module_name: str
    total_lines: int
    is_test_file: bool
    imports: List[ImportInfo] = field(default_factory=list)
    symbols: List[SymbolInfo] = field(default_factory=list)
    syntax_error: Optional[str] = None

class CallVisitor(ast.NodeVisitor):
    """AST visitor to extract function and method calls inside a code block."""
    def __init__(self):
        self.calls: List[CallInfo] = []

    def visit_Call(self, node: ast.Call):
        callee_name = ""
        is_method = False
        object_name = None

        if isinstance(node.func, ast.Name):
            callee_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            callee_name = node.func.attr
            is_method = True
            if isinstance(node.func.value, ast.Name):
                object_name = node.func.value.id
            elif isinstance(node.func.value, ast.Attribute):
                # nested attribute like a.b.c()
                object_name = self._resolve_attribute(node.func.value)
        
        if callee_name:
            self.calls.append(
                CallInfo(
                    callee_name=callee_name,
                    line_number=node.lineno,
                    is_method=is_method,
                    object_name=object_name,
                    unresolved=True,
                )
            )
        self.generic_visit(node)

    def _resolve_attribute(self, node: ast.Attribute) -> str:
        parts = []
        curr = node
        while isinstance(curr, ast.Attribute):
            parts.append(curr.attr)
            curr = curr.value
        if isinstance(curr, ast.Name):
            parts.append(curr.id)
        return ".".join(reversed(parts))

class PythonRepositoryParser:
    """Parses Python repository source code into AST models with import and call resolution."""

    def __init__(self, root_dir: str):
        self.root_dir = os.path.abspath(root_dir)
        self.parsed_files: Dict[str, ParsedFile] = {}

    def is_test_file(self, rel_path: str) -> bool:
        normalized = rel_path.replace("\\", "/").lower()
        base = os.path.basename(normalized)
        return (
            base.startswith("test_")
            or base.endswith("_test.py")
            or "/tests/" in normalized
            or "/test/" in normalized
        )

    def path_to_module_name(self, rel_path: str) -> str:
        clean = rel_path.replace("\\", "/")
        if clean.endswith(".py"):
            clean = clean[:-3]
        if clean.endswith("/__init__"):
            clean = clean[:-9]
        return clean.replace("/", ".")

    def parse_file(self, rel_path: str, full_path: str) -> ParsedFile:
        normalized_rel = rel_path.replace("\\", "/")
        is_test = self.is_test_file(normalized_rel)
        module_name = self.path_to_module_name(normalized_rel)

        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            return ParsedFile(
                file_path=normalized_rel,
                module_name=module_name,
                total_lines=0,
                is_test_file=is_test,
                syntax_error=str(e),
            )

        total_lines = len(content.splitlines())

        try:
            tree = ast.parse(content, filename=full_path)
        except SyntaxError as se:
            return ParsedFile(
                file_path=normalized_rel,
                module_name=module_name,
                total_lines=total_lines,
                is_test_file=is_test,
                syntax_error=f"SyntaxError at line {se.lineno}: {se.msg}",
            )

        imports: List[ImportInfo] = []
        symbols: List[SymbolInfo] = []

        # Extract module-level imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(
                        ImportInfo(
                            module=alias.name,
                            alias=alias.asname,
                            line_number=node.lineno,
                        )
                    )
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                level = node.level
                for alias in node.names:
                    imports.append(
                        ImportInfo(
                            module=mod,
                            imported_name=alias.name,
                            alias=alias.asname,
                            is_relative=(level > 0),
                            relative_level=level,
                            line_number=node.lineno,
                        )
                    )

        # Extract Classes and Functions
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                class_doc = ast.get_docstring(node)
                class_id = f"{normalized_rel}:{node.name}"
                class_sym = SymbolInfo(
                    id=class_id,
                    name=node.name,
                    qualified_name=f"{module_name}.{node.name}",
                    symbol_type="class",
                    file_path=normalized_rel,
                    start_line=node.lineno,
                    end_line=getattr(node, "end_lineno", node.lineno),
                    docstring=class_doc,
                    is_test=node.name.startswith("Test") or is_test,
                )
                symbols.append(class_sym)

                # Process Methods
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_doc = ast.get_docstring(item)
                        method_id = f"{normalized_rel}:{node.name}.{item.name}"
                        params = [arg.arg for arg in item.args.args]
                        
                        # Extract calls
                        cv = CallVisitor()
                        cv.visit(item)

                        is_method_test = (
                            item.name.startswith("test_")
                            or item.name.startswith("test")
                            or class_sym.is_test
                        )

                        method_sym = SymbolInfo(
                            id=method_id,
                            name=item.name,
                            qualified_name=f"{module_name}.{node.name}.{item.name}",
                            symbol_type="method",
                            file_path=normalized_rel,
                            start_line=item.lineno,
                            end_line=getattr(item, "end_lineno", item.lineno),
                            docstring=method_doc,
                            parameters=params,
                            class_name=node.name,
                            is_test=is_method_test,
                            calls=cv.calls,
                        )
                        symbols.append(method_sym)

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fn_doc = ast.get_docstring(node)
                fn_id = f"{normalized_rel}:{node.name}"
                params = [arg.arg for arg in node.args.args]

                # Extract calls inside function
                cv = CallVisitor()
                cv.visit(node)

                is_fn_test = (
                    node.name.startswith("test_")
                    or node.name.startswith("test")
                    or is_test
                )

                fn_sym = SymbolInfo(
                    id=fn_id,
                    name=node.name,
                    qualified_name=f"{module_name}.{node.name}",
                    symbol_type="function",
                    file_path=normalized_rel,
                    start_line=node.lineno,
                    end_line=getattr(node, "end_lineno", node.lineno),
                    docstring=fn_doc,
                    parameters=params,
                    is_test=is_fn_test,
                    calls=cv.calls,
                )
                symbols.append(fn_sym)

        parsed = ParsedFile(
            file_path=normalized_rel,
            module_name=module_name,
            total_lines=total_lines,
            is_test_file=is_test,
            imports=imports,
            symbols=symbols,
        )
        return parsed

    def parse_all(self, file_paths: List[str]) -> Dict[str, ParsedFile]:
        """Parse all supplied relative file paths."""
        for rel_path in file_paths:
            full_path = os.path.join(self.root_dir, rel_path)
            if os.path.exists(full_path):
                self.parsed_files[rel_path] = self.parse_file(rel_path, full_path)
        
        # After all files are parsed, resolve calls across files
        self.resolve_calls()
        return self.parsed_files

    def resolve_calls(self):
        """
        Cross-reference AST calls against defined symbols and imports.
        Resolves callee_name to target symbol id deterministically.
        """
        # Build quick symbol lookup tables
        # by_id: id -> SymbolInfo
        # by_file_and_name: (file_path, symbol_name) -> SymbolInfo
        # by_module_and_name: (module_name, symbol_name) -> SymbolInfo
        # by_name_global: symbol_name -> List[SymbolInfo]
        by_file_and_name: Dict[tuple, SymbolInfo] = {}
        by_module_and_name: Dict[tuple, SymbolInfo] = {}
        by_name_global: Dict[str, List[SymbolInfo]] = {}

        for parsed in self.parsed_files.values():
            for sym in parsed.symbols:
                by_file_and_name[(sym.file_path, sym.name)] = sym
                by_module_and_name[(parsed.module_name, sym.name)] = sym
                if sym.class_name:
                    by_file_and_name[(sym.file_path, f"{sym.class_name}.{sym.name}")] = sym
                    by_module_and_name[(parsed.module_name, f"{sym.class_name}.{sym.name}")] = sym
                by_name_global.setdefault(sym.name, []).append(sym)

        for parsed in self.parsed_files.values():
            # Build import map for this file: alias_or_name -> (module, original_name)
            import_map: Dict[str, tuple] = {}
            for imp in parsed.imports:
                if imp.imported_name:
                    lookup_key = imp.alias or imp.imported_name
                    target_module = imp.module
                    if imp.is_relative:
                        # resolve relative module
                        parts = parsed.module_name.split(".")
                        base_parts = parts[:-imp.relative_level] if imp.relative_level <= len(parts) else []
                        if target_module:
                            target_module = ".".join(base_parts + [target_module])
                        else:
                            target_module = ".".join(base_parts)
                    import_map[lookup_key] = (target_module, imp.imported_name)
                else:
                    lookup_key = imp.alias or imp.module.split(".")[-1]
                    import_map[lookup_key] = (imp.module, None)

            for sym in parsed.symbols:
                for call in sym.calls:
                    # Strategy 1: Local function or method call (including self.method())
                    if (sym.file_path, call.callee_name) in by_file_and_name:
                        target = by_file_and_name[(sym.file_path, call.callee_name)]
                        call.resolved_symbol_id = target.id
                        call.unresolved = False
                        continue
                    
                    # Handle self.method() calls
                    if call.object_name == 'self' and call.is_method:
                        # Search for a method with the same name in the same file
                        # (simplification: assume the first match in the same file is correct)
                        # A better way would be to check if the current symbol is a method of a class
                        # and if the callee is another method of that same class.
                        if (sym.file_path, call.callee_name) in by_file_and_name:
                            target = by_file_and_name[(sym.file_path, call.callee_name)]
                            call.resolved_symbol_id = target.id
                            call.unresolved = False
                            continue

                    # Strategy 2: Directly imported function name (e.g. from auth.security import authenticate_user)
                    if call.callee_name in import_map:
                        mod, orig_name = import_map[call.callee_name]
                        search_name = orig_name or call.callee_name
                        if (mod, search_name) in by_module_and_name:
                            target = by_module_and_name[(mod, search_name)]
                            call.resolved_symbol_id = target.id
                            call.unresolved = False
                            continue

                    # Strategy 3: Called via module attribute (e.g. security.authenticate_user() where import security)
                    if call.object_name and call.object_name in import_map:
                        mod, _ = import_map[call.object_name]
                        if (mod, call.callee_name) in by_module_and_name:
                            target = by_module_and_name[(mod, call.callee_name)]
                            call.resolved_symbol_id = target.id
                            call.unresolved = False
                            continue

                    # Strategy 4: Unambiguous global match if symbol name is unique across repo
                    candidates = by_name_global.get(call.callee_name, [])
                    if len(candidates) == 1 and not call.is_method:
                        call.resolved_symbol_id = candidates[0].id
                        call.unresolved = False
                        continue

                    # Otherwise, marked unresolved (never invent edges)
                    call.unresolved = True
