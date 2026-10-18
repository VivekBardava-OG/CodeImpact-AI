import logging
from typing import Dict, List, Any, Optional, Set
from app.core.db import db_manager

logger = logging.getLogger("codeimpact.impact_engine")

class ImpactAnalysisEngine:
    """Graph-powered impact analysis engine running bounded Cypher queries on FalkorDB."""

    def __init__(self, db=db_manager):
        self.db = db

    def get_graph_name(self, repo_id: str) -> str:
        clean = repo_id.replace("-", "_").replace(".", "_")
        return f"repo_{clean}"

    def analyze_symbol_impact(
        self,
        repo_id: str,
        symbol_id: str,
        max_hops: int = 5,
    ) -> Dict[str, Any]:
        """
        Perform complete impact analysis for a given symbol in the repository graph.
        Returns directly impacted, transitively impacted, affected tests, paths, and graph visualization slice.
        """
        graph_name = self.get_graph_name(repo_id)

        # 1. Fetch Target Symbol Details
        target_query = """
        MATCH (target:Symbol {id: $symbol_id})
        RETURN target.id, target.name, target.qualified_name, target.symbol_type,
               target.file_path, target.start_line, target.end_line,
               target.parameters, target.docstring
        """
        target_rows = self.db.execute_query(graph_name, target_query, {"symbol_id": symbol_id})
        if not target_rows:
            # Check if it was a Test node
            test_query = """
            MATCH (target:Test {id: $symbol_id})
            RETURN target.id, target.name, target.qualified_name, 'test' as symbol_type,
                   target.file_path, target.start_line, target.end_line,
                   '' as parameters, target.docstring
            """
            target_rows = self.db.execute_query(graph_name, test_query, {"symbol_id": symbol_id})
            if not target_rows:
                raise ValueError(f"Symbol with ID '{symbol_id}' was not found in graph '{graph_name}'.")

        t_row = target_rows[0]
        target_info = {
            "id": t_row[0],
            "name": t_row[1],
            "qualified_name": t_row[2],
            "symbol_type": t_row[3],
            "file_path": t_row[4],
            "start_line": t_row[5],
            "end_line": t_row[6],
            "parameters": t_row[7],
            "docstring": t_row[8],
        }

        # 2. Query Transitive Callers (bounded traversal 1..max_hops)
        # Handles cycles and prevents runaway queries with bounded hop paths
        path_query = f"""
        MATCH p = (caller)-[:CALLS*1..{max_hops}]->(target:Symbol {{id: $symbol_id}})
        WHERE caller <> target
        RETURN caller.id, caller.name, caller.qualified_name, caller.file_path,
               coalesce(caller.symbol_type, 'test') as symbol_type,
               labels(caller) as caller_labels,
               length(p) as hop_count,
               [n in nodes(p) | {{id: n.id, name: n.name, type: coalesce(n.symbol_type, 'test'), file_path: n.file_path}}] as path_nodes
        ORDER BY hop_count ASC
        """
        path_rows = self.db.execute_query(graph_name, path_query, {"symbol_id": symbol_id})

        # Process Dependents (direct vs indirect)
        direct_dependents: List[Dict[str, Any]] = []
        indirect_dependents: List[Dict[str, Any]] = []
        seen_dependents: Set[str] = set()

        shortest_paths: Dict[str, List[Dict[str, Any]]] = {}

        for row in path_rows:
            cid, cname, cqname, cfile, ctype, clabels, hop, pnodes = row
            if cid in seen_dependents:
                continue
            seen_dependents.add(cid)

            item = {
                "id": cid,
                "name": cname,
                "qualified_name": cqname,
                "file_path": cfile,
                "symbol_type": ctype,
                "is_test": ("Test" in clabels or ctype == "test"),
                "hop_count": hop,
                "impact_type": "direct" if hop == 1 else "indirect",
                "confidence": "high" if hop == 1 else ("medium" if hop == 2 else "low"),
                "path": pnodes,
            }
            shortest_paths[cid] = pnodes

            if hop == 1:
                direct_dependents.append(item)
            else:
                indirect_dependents.append(item)

        # 3. Discover Potentially Affected Tests
        test_query = f"""
        MATCH p = (t:Test)-[:TESTS|CALLS*1..{max_hops}]->(target:Symbol {{id: $symbol_id}})
        RETURN t.id, t.name, t.qualified_name, t.file_path, t.start_line, t.end_line,
               length(p) as hop_count,
               [n in nodes(p) | {{id: n.id, name: n.name, type: coalesce(n.symbol_type, 'test')}}] as path_nodes
        ORDER BY hop_count ASC
        """
        test_rows = self.db.execute_query(graph_name, test_query, {"symbol_id": symbol_id})

        affected_tests: List[Dict[str, Any]] = []
        seen_tests: Set[str] = set()

        for trow in test_rows:
            tid, tname, tqname, tfile, tstart, tend, thop, tpnodes = trow
            if tid in seen_tests:
                continue
            seen_tests.add(tid)

            if thop == 1:
                confidence = "high"
                recommendation_reason = (
                    f"Directly calls and exercises '{target_info['name']}'. High probability of regression if contract changes."
                )
            else:
                intermediate = tpnodes[1]["name"] if len(tpnodes) > 1 else "upstream component"
                confidence = "medium" if thop == 2 else "suggested"
                recommendation_reason = (
                    f"Tests '{intermediate}' which transitively invokes '{target_info['name']}' ({thop} graph hops away)."
                )

            affected_tests.append({
                "id": tid,
                "name": tname,
                "qualified_name": tqname,
                "file_path": tfile,
                "start_line": tstart,
                "end_line": tend,
                "hop_count": thop,
                "confidence": confidence,
                "recommendation_reason": recommendation_reason,
                "path": tpnodes,
                "execution_status": "NOT_EXECUTED", # Explicitly distinguished from executed tests
            })

        # 4. Directly & Indirectly Affected Files
        affected_files_map: Dict[str, Dict[str, Any]] = {}
        target_file = target_info["file_path"]

        affected_files_map[target_file] = {
            "file_path": target_file,
            "impact_type": "origin",
            "hop_count": 0,
            "affected_symbols_count": 1,
            "affected_symbols": [target_info["name"]],
        }

        for dep in direct_dependents + indirect_dependents:
            fpath = dep["file_path"]
            if fpath not in affected_files_map:
                affected_files_map[fpath] = {
                    "file_path": fpath,
                    "impact_type": dep["impact_type"],
                    "hop_count": dep["hop_count"],
                    "affected_symbols_count": 0,
                    "affected_symbols": [],
                }
            affected_files_map[fpath]["affected_symbols_count"] += 1
            affected_files_map[fpath]["affected_symbols"].append(dep["name"])

        # 5. High-Impact Shared Modules (Centrality in this repo)
        centrality_query = """
        MATCH (s:Symbol)<-[:CALLS]-(caller)
        WITH s, count(caller) as in_degree
        WHERE in_degree >= 1
        RETURN s.id, s.name, s.file_path, in_degree
        ORDER BY in_degree DESC LIMIT 5
        """
        centrality_rows = self.db.execute_query(graph_name, centrality_query)
        high_impact_modules = [
            {
                "symbol_id": crow[0],
                "name": crow[1],
                "file_path": crow[2],
                "dependent_callers_count": crow[3],
                "is_target": (crow[0] == symbol_id),
            }
            for crow in centrality_rows
        ]

        # 6. Extract Subgraph for React Flow Visualization
        graph_visualization = self._build_impact_graph_visualization(
            target_info, direct_dependents, indirect_dependents, affected_tests
        )

        # 7. Summary Risk Metric
        total_affected_symbols = len(direct_dependents) + len(indirect_dependents)
        total_affected_tests = len(affected_tests)
        total_affected_files = len(affected_files_map)

        # Transparent risk assessment based on verified evidence
        risk_evidence = []
        if total_affected_symbols > 0:
            risk_evidence.append(f"{total_affected_symbols} symbols affected")
        if total_affected_tests > 0:
            risk_evidence.append(f"{total_affected_tests} tests affected")
        if total_affected_files > 1:
            risk_evidence.append(f"Spans {total_affected_files} files")

        if not risk_evidence:
            blast_radius_risk = "LOW"
            risk_evidence.append("No dependents found in current graph")
        elif total_affected_symbols > 5 or total_affected_tests > 3:
            blast_radius_risk = "HIGH"
        elif total_affected_symbols > 2 or total_affected_tests > 1:
            blast_radius_risk = "MEDIUM"
        else:
            blast_radius_risk = "LOW"

        return {
            "target": target_info,
            "blast_radius_risk": blast_radius_risk,
            "risk_evidence": "; ".join(risk_evidence),
            "metrics": {
                "total_affected_symbols": total_affected_symbols,
                "direct_dependents_count": len(direct_dependents),
                "indirect_dependents_count": len(indirect_dependents),
                "potentially_affected_tests_count": total_affected_tests,
                "affected_files_count": total_affected_files,
                "max_graph_hops": max([d["hop_count"] for d in direct_dependents + indirect_dependents], default=0),
            },
            "direct_dependents": direct_dependents,
            "indirect_dependents": indirect_dependents,
            "affected_tests": affected_tests,
            "affected_files": list(affected_files_map.values()),
            "high_impact_shared_modules": high_impact_modules,
            "visualization": graph_visualization,
        }

    def _build_impact_graph_visualization(
        self,
        target: Dict[str, Any],
        direct_deps: List[Dict[str, Any]],
        indirect_deps: List[Dict[str, Any]],
        affected_tests: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Format impact graph nodes and edges into a layout for React Flow."""
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []
        node_ids: Set[str] = set()

        # Add Target Node
        nodes.append({
            "id": target["id"],
            "type": "targetNode",
            "data": {
                "label": target["name"],
                "sublabel": target["file_path"],
                "symbol_type": target["symbol_type"],
                "role": "target",
                "isTarget": True,
            },
            "position": {"x": 400, "y": 300},
        })
        node_ids.add(target["id"])

        # Layout dependents in concentric/layered columns
        all_deps = direct_deps + indirect_deps
        for i, dep in enumerate(all_deps):
            if dep["id"] not in node_ids:
                node_type = "testNode" if dep["is_test"] else "dependentNode"
                hop = dep["hop_count"]
                
                # Arrange horizontally based on hop count
                x_pos = 400 - (hop * 240) if hop % 2 == 1 else 400 + (hop * 240)
                y_pos = 120 + (i * 90)

                nodes.append({
                    "id": dep["id"],
                    "type": node_type,
                    "data": {
                        "label": dep["name"],
                        "sublabel": dep["file_path"],
                        "symbol_type": dep["symbol_type"],
                        "hop_count": dep["hop_count"],
                        "impact_type": dep["impact_type"],
                        "confidence": dep["confidence"],
                    },
                    "position": {"x": x_pos, "y": y_pos},
                })
                node_ids.add(dep["id"])

        # Add Test nodes
        for j, test in enumerate(affected_tests):
            if test["id"] not in node_ids:
                nodes.append({
                    "id": test["id"],
                    "type": "testNode",
                    "data": {
                        "label": test["name"],
                        "sublabel": test["file_path"],
                        "symbol_type": "test",
                        "hop_count": test["hop_count"],
                        "confidence": test["confidence"],
                        "status": "NOT_EXECUTED",
                    },
                    "position": {"x": 750, "y": 100 + (j * 110)},
                })
                node_ids.add(test["id"])

        # Build Edges based on paths
        edge_ids: Set[str] = set()
        for item in all_deps + affected_tests:
            path = item.get("path", [])
            for k in range(len(path) - 1):
                source_id = path[k]["id"]
                dest_id = path[k + 1]["id"]
                edge_id = f"e_{source_id}->{dest_id}"
                if edge_id not in edge_ids and source_id in node_ids and dest_id in node_ids:
                    edge_ids.add(edge_id)
                    edges.append({
                        "id": edge_id,
                        "source": source_id,
                        "target": dest_id,
                        "animated": True,
                        "label": "CALLS" if item.get("symbol_type") != "test" else "TESTS",
                        "style": {"stroke": "#f59e0b" if item.get("impact_type") == "direct" else "#6366f1"},
                    })

        return {"nodes": nodes, "edges": edges}

impact_engine = ImpactAnalysisEngine()
