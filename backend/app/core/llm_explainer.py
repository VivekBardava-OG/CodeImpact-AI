import logging
from typing import Dict, Any, List, Optional
from app.config import settings

logger = logging.getLogger("codeimpact.llm_explainer")

class ImpactExplainerService:
    """Provides deterministic and LLM-augmented explanations grounded in FalkorDB graph facts."""

    def __init__(self):
        self.gemini_configured = bool(settings.gemini_api_key)

    def generate_deterministic_explanation(self, impact_data: Dict[str, Any]) -> str:
        """
        Produce a comprehensive, structured explanation derived directly from FalkorDB query results.
        No LLM API key required.
        """
        target = impact_data["target"]
        direct = impact_data["direct_dependents"]
        indirect = impact_data["indirect_dependents"]
        tests = impact_data["affected_tests"]
        risk = impact_data["blast_radius_risk"]

        lines: List[str] = []
        lines.append(f"### 🛡️ CodeImpact Analysis: `{target['name']}`")
        lines.append(f"- **Target File:** `{target['file_path']}` (Lines {target['start_line']}–{target['end_line']})")
        lines.append(f"- **Symbol Type:** {target['symbol_type'].capitalize()}")
        lines.append(f"- **Blast Radius Risk:** **{risk}**\n")

        # 1. Direct Callers
        lines.append("#### 1. Verified Direct Dependents (1 Graph Hop)")
        if direct:
            for dep in direct:
                lines.append(
                    f"- **`{dep['name']}`** in `{dep['file_path']}` ({dep['symbol_type']}) — *Verified direct caller via FalkorDB `[:CALLS]` edge*"
                )
        else:
            lines.append("- *No direct callers detected in the indexed repository.*")
        lines.append("")

        # 2. Indirect Callers
        lines.append("#### 2. Transitive Indirect Dependents (2+ Graph Hops)")
        if indirect:
            for dep in indirect:
                path_str = " ➔ ".join([node["name"] for node in dep["path"]])
                lines.append(
                    f"- **`{dep['name']}`** in `{dep['file_path']}` ({dep['hop_count']} hops away)\n"
                    f"  - *Call Path:* `{path_str}`"
                )
        else:
            lines.append("- *No indirect dependents found within the traversal limit.*")
        lines.append("")

        # 3. Potentially Affected Tests
        lines.append("#### 3. Recommended Tests (Based on Graph Connectivity)")
        if tests:
            for test in tests:
                conf = test["confidence"].upper()
                lines.append(
                    f"- **`{test['name']}`** (`{test['file_path']}`) — **[{conf} CONFIDENCE]**\n"
                    f"  - *Rationale:* {test['recommendation_reason']}\n"
                    f"  - *Status:* `NOT_EXECUTED` (Recommended to run before merging)"
                )
        else:
            lines.append("- *No automated tests were found directly or transitively covering this symbol.*")
            lines.append("  ⚠️ **Action Required:** Consider adding unit tests for this function to prevent regressions.")
        lines.append("")

        # 4. Verification Statement
        lines.append("---")
        lines.append(
            "> **Integrity Notice:** All relationships above are deterministic graph facts retrieved from FalkorDB Cypher queries. "
            "Tests are recommended based on static call graph reachability and have not been executed."
        )

        return "\n".join(lines)

    async def answer_question(
        self,
        question: str,
        impact_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Answer a natural language question about the impact graph.
        If Gemini API key is configured, uses LLM grounded with graph data.
        Otherwise, uses deterministic query-backed response engine.
        """
        deterministic_summary = self.generate_deterministic_explanation(impact_data)

        if not settings.gemini_api_key:
            return {
                "answer": deterministic_summary,
                "source": "deterministic_graph_engine",
                "model": "falkordb_cypher_grounded",
                "grounded_facts": {
                    "direct_count": len(impact_data["direct_dependents"]),
                    "indirect_count": len(impact_data["indirect_dependents"]),
                    "tests_count": len(impact_data["affected_tests"]),
                },
            }

        # If Gemini API key is present, invoke Google GenAI
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            model = genai.GenerativeModel(settings.llm_model)

            prompt = f"""
You are CodeImpact AI, an expert software architecture agent explaining real FalkorDB graph query results to a developer.

RULES:
1. ONLY use the verified graph data provided below.
2. NEVER invent dependencies, files, or relationships.
3. ALWAYS clearly distinguish between verified facts from the graph and suggested next steps.
4. If asked about tests, state that they are RECOMMENDED to run and have NOT been executed yet.

GRAPH ANALYSIS DATA FROM FALKORDB:
Target Symbol: {impact_data['target']['name']} ({impact_data['target']['symbol_type']}) in {impact_data['target']['file_path']}
Direct Dependents: {[d['name'] + ' in ' + d['file_path'] for d in impact_data['direct_dependents']]}
Indirect Dependents: {[d['name'] + ' (' + str(d['hop_count']) + ' hops) in ' + d['file_path'] for d in impact_data['indirect_dependents']]}
Recommended Tests: {[t['name'] + ' in ' + t['file_path'] + ' (' + t['confidence'] + ')' for t in impact_data['affected_tests']]}
High Impact Shared Modules: {[m['name'] for m in impact_data.get('high_impact_shared_modules', [])]}

USER QUESTION:
{question}

Provide a clear, developer-friendly response directly addressing their question using the graph facts.
"""
            response = await model.generate_content_async(prompt)
            return {
                "answer": response.text,
                "source": "llm_grounded",
                "model": settings.llm_model,
                "grounded_facts": {
                    "direct_count": len(impact_data["direct_dependents"]),
                    "indirect_count": len(impact_data["indirect_dependents"]),
                    "tests_count": len(impact_data["affected_tests"]),
                },
            }
        except Exception as e:
            logger.warning(f"LLM generation failed, falling back to deterministic explanation: {e}")
            return {
                "answer": deterministic_summary + f"\n\n*(Note: LLM provider unavailable: {e}; fell back to FalkorDB deterministic engine)*",
                "source": "deterministic_fallback",
                "model": "falkordb_cypher_grounded",
                "grounded_facts": {
                    "direct_count": len(impact_data["direct_dependents"]),
                    "indirect_count": len(impact_data["indirect_dependents"]),
                    "tests_count": len(impact_data["affected_tests"]),
                },
            }

explainer_service = ImpactExplainerService()
