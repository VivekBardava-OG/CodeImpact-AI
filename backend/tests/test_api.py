import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["connected"] is True

def test_api_list_repositories():
    res = client.get("/api/repositories")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert any(r["repo_id"] == "sample-auth-service" for r in data)

def test_api_index_and_analyze_flow():
    # 1. Index sample repository
    index_res = client.post("/api/repositories/sample-auth-service/index")
    assert index_res.status_code == 200
    index_data = index_res.json()
    assert index_data["total_files"] >= 6
    assert index_data["total_symbols"] >= 8

    # 2. Get list of symbols
    symbols_res = client.get("/api/repositories/sample-auth-service/symbols")
    assert symbols_res.status_code == 200
    symbols_data = symbols_res.json()
    auth_sym = next(s for s in symbols_data["symbols"] if s["name"] == "authenticate_user")
    assert auth_sym is not None

    # 3. Analyze impact
    impact_res = client.post(
        "/api/impact/analyze",
        json={"repo_id": "sample-auth-service", "symbol_id": auth_sym["id"], "max_hops": 5},
    )
    assert impact_res.status_code == 200
    impact_data = impact_res.json()
    assert impact_data["target"]["name"] == "authenticate_user"
    assert len(impact_data["direct_dependents"]) >= 1
    assert len(impact_data["affected_tests"]) >= 2
    assert "explanation" in impact_data

    # 4. Ask natural language question
    ask_res = client.post(
        "/api/impact/ask",
        json={
            "repo_id": "sample-auth-service",
            "symbol_id": auth_sym["id"],
            "question": "Which tests should I run if I change this function?",
        },
    )
    assert ask_res.status_code == 200
    ask_data = ask_res.json()
    assert "answer" in ask_data
    assert "test_authenticate_user_success" in ask_data["answer"]

def test_api_diff_analysis():
    diff_sample = """diff --git a/auth/security.py b/auth/security.py
index abc..def 100644
--- a/auth/security.py
+++ b/auth/security.py
@@ -20,3 +20,4 @@ def authenticate_user(username: str, password: str) -> Optional[User]:
+    # Modified authenticate_user contract
"""
    res = client.post(
        "/api/impact/diff",
        json={"repo_id": "sample-auth-service", "diff_text": diff_sample},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["changed_files_count"] == 1
    assert data["changed_symbols_count"] >= 1
    changed_names = [s["name"] for s in data["changed_symbols"]]
    assert "authenticate_user" in changed_names
