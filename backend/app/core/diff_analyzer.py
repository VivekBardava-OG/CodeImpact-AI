import re
import logging
from typing import Dict, List, Any, Set, Tuple
from app.core.db import db_manager
from app.core.impact_engine import impact_engine

logger = logging.getLogger("codeimpact.diff_analyzer")

class GitDiffAnalyzer:
    """Parses standard Git diffs and maps modified lines to FalkorDB symbols and affected tests."""

    def __init__(self, db=db_manager):
        self.db = db

    def parse_diff(self, diff_text: str) -> Dict[str, List[int]]:
        """
        Parse unified git diff format to extract modified line numbers per file.
        Returns mapping: file_path -> list of modified line numbers.
        """
        file_modifications: Dict[str, List[int]] = {}
        current_file = None
        current_new_line = 0

        # Pattern for diff header: +++ b/path/to/file.py
        file_header_pattern = re.compile(r"^\+\+\+\s+b/(.+)$")
        # Pattern for hunk header: @@ -old_start,old_count +new_start,new_count @@
        hunk_header_pattern = re.compile(r"^@@\s+-\d+(?:,\d+)?\s+\+(\d+)(?:,(\d+))?\s+@@")

        for line in diff_text.splitlines():
            file_match = file_header_pattern.match(line)
            if file_match:
                current_file = file_match.group(1).strip()
                if current_file.endswith(".py"):
                    file_modifications.setdefault(current_file, [])
                else:
                    current_file = None
                continue

            hunk_match = hunk_header_pattern.match(line)
            if hunk_match and current_file:
                current_new_line = int(hunk_match.group(1))
                continue

            if current_file and current_new_line > 0:
                if line.startswith("+") and not line.startswith("+++"):
                    file_modifications[current_file].append(current_new_line)
                    current_new_line += 1
                elif line.startswith("-") and not line.startswith("---"):
                    # Deleted line, does not advance new file line counter
                    pass
                else:
                    # Context line
                    current_new_line += 1

        return file_modifications

    def analyze_diff(self, repo_id: str, diff_text: str) -> Dict[str, Any]:
        """
        Analyze complete diff against FalkorDB graph.
        Maps modified line numbers to symbols, then computes aggregate blast radius.
        """
        graph_name = f"repo_{repo_id.replace('-', '_').replace('.', '_')}"
        file_mods = self.parse_diff(diff_text)

        if not file_mods:
            return {
                "changed_files_count": 0,
                "changed_symbols_count": 0,
                "changed_symbols": [],
                "aggregate_affected_symbols": [],
                "aggregate_affected_tests": [],
                "message": "No Python file modifications detected in the supplied diff.",
            }

        changed_symbols: List[Dict[str, Any]] = []
        seen_sym_ids: Set[str] = set()

        for file_path, lines in file_mods.items():
            if not lines:
                continue

            # Find all symbols in this file that enclose any modified line
            symbol_query = """
            MATCH (s:Symbol {file_path: $file_path, repo_id: $repo_id})
            RETURN s.id, s.name, s.qualified_name, s.start_line, s.end_line, s.symbol_type
            """
            rows = self.db.execute_query(graph_name, symbol_query, {"file_path": file_path, "repo_id": repo_id})

            for s_id, s_name, s_qname, s_start, s_end, s_type in rows:
                if s_id in seen_sym_ids:
                    continue
                # Check overlap
                for line_no in lines:
                    if s_start <= line_no <= s_end:
                        changed_symbols.append({
                            "id": s_id,
                            "name": s_name,
                            "qualified_name": s_qname,
                            "file_path": file_path,
                            "symbol_type": s_type,
                            "start_line": s_start,
                            "end_line": s_end,
                            "modified_line": line_no,
                        })
                        seen_sym_ids.add(s_id)
                        break

        # Compute combined impact across all identified symbols
        all_affected_symbols_map: Dict[str, Dict[str, Any]] = {}
        all_affected_tests_map: Dict[str, Dict[str, Any]] = {}

        for sym in changed_symbols:
            try:
                impact = impact_engine.analyze_symbol_impact(repo_id, sym["id"])
                for dep in impact["direct_dependents"] + impact["indirect_dependents"]:
                    all_affected_symbols_map[dep["id"]] = dep
                for test in impact["affected_tests"]:
                    all_affected_tests_map[test["id"]] = test
            except Exception as e:
                logger.warning(f"Error computing impact for diff symbol {sym['id']}: {e}")

        return {
            "changed_files_count": len(file_mods),
            "changed_files": list(file_mods.keys()),
            "changed_symbols_count": len(changed_symbols),
            "changed_symbols": changed_symbols,
            "aggregate_affected_symbols_count": len(all_affected_symbols_map),
            "aggregate_affected_symbols": list(all_affected_symbols_map.values()),
            "aggregate_affected_tests_count": len(all_affected_tests_map),
            "aggregate_affected_tests": list(all_affected_tests_map.values()),
        }

diff_analyzer = GitDiffAnalyzer()
