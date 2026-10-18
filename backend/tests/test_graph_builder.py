import os
import pytest
from app.core.parser import PythonRepositoryParser
from app.core.graph_builder import graph_builder
from app.core.db import db_manager

FIXTURE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "fixtures", "sample_project")
)

def test_graph_builder_and_idempotency():
    # 1. Parse fixture files
    parser = PythonRepositoryParser(FIXTURE_DIR)
    files = [
        "models/user.py",
        "db/database.py",
        "auth/security.py",
        "services/user_service.py",
        "api/auth_controller.py",
        "tests/test_auth.py",
    ]
    parsed = parser.parse_all(files)
    repo_id = "test_build_repo"

    # 2. First Build
    result1 = graph_builder.build_graph(
        repo_id=repo_id,
        repo_name="Test Repo",
        repo_path=FIXTURE_DIR,
        parsed_files=parsed,
    )
    assert result1["total_files"] == 6
    assert result1["total_symbols"] > 0
    assert result1["total_tests"] > 0
    assert result1["resolved_calls"] > 0

    # 3. Second Build (Verify Idempotency - duplicate nodes prevented by clean wipe/merge)
    result2 = graph_builder.build_graph(
        repo_id=repo_id,
        repo_name="Test Repo",
        repo_path=FIXTURE_DIR,
        parsed_files=parsed,
    )
    assert result2["total_files"] == result1["total_files"]
    assert result2["total_symbols"] == result1["total_symbols"]
    assert result2["total_tests"] == result1["total_tests"]

    # 4. Verify Nodes exist in FalkorDB via Cypher
    graph_name = f"repo_{repo_id}"
    rows = db_manager.execute_query(graph_name, "MATCH (s:Symbol {name: 'authenticate_user'}) RETURN s.id")
    assert len(rows) == 1
    assert rows[0][0] == f"{repo_id}:auth/security.py:authenticate_user"
