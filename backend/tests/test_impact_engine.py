import os
import pytest
from app.core.parser import PythonRepositoryParser
from app.core.graph_builder import graph_builder
from app.core.impact_engine import impact_engine

FIXTURE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "fixtures", "sample_project")
)

@pytest.fixture(scope="module")
def setup_indexed_sample_repo():
    repo_id = "test_impact_fixture"
    parser = PythonRepositoryParser(FIXTURE_DIR)
    files = [
        "models/user.py",
        "db/database.py",
        "auth/security.py",
        "services/user_service.py",
        "api/auth_controller.py",
        "api/payment_controller.py",
        "tests/test_auth.py",
        "tests/test_api.py",
    ]
    parsed = parser.parse_all(files)
    graph_builder.build_graph(
        repo_id=repo_id,
        repo_name="Sample Project",
        repo_path=FIXTURE_DIR,
        parsed_files=parsed,
    )
    return repo_id

def test_direct_and_indirect_impact_analysis(setup_indexed_sample_repo):
    repo_id = setup_indexed_sample_repo
    target_id = f"{repo_id}:auth/security.py:authenticate_user"

    impact = impact_engine.analyze_symbol_impact(repo_id, target_id)

    # 1. Target details
    assert impact["target"]["name"] == "authenticate_user"

    # 2. Direct Dependents (login_user calls authenticate_user)
    direct_names = [d["name"] for d in impact["direct_dependents"]]
    assert "login_user" in direct_names

    # 3. Indirect Dependents (handle_login_request calls login_user, 2 hops)
    indirect_names = [d["name"] for d in impact["indirect_dependents"]]
    assert "handle_login_request" in indirect_names
    handle_login = next(d for d in impact["indirect_dependents"] if d["name"] == "handle_login_request")
    assert handle_login["hop_count"] == 2

    # 4. Potentially Affected Tests
    affected_test_names = [t["name"] for t in impact["affected_tests"]]
    # Directly tests authenticate_user:
    assert "test_authenticate_user_success" in affected_test_names
    assert "test_authenticate_user_invalid_password" in affected_test_names
    # Indirectly tests through handle_login_request:
    assert "test_login_endpoint" in affected_test_names

    # 5. Risk Assessment
    assert impact["blast_radius_risk"] in ["CRITICAL", "MODERATE", "LOW"]

    # 6. Visualization Data
    vis = impact["visualization"]
    assert len(vis["nodes"]) > 0
    assert len(vis["edges"]) > 0

def test_missing_symbol_raises_value_error(setup_indexed_sample_repo):
    repo_id = setup_indexed_sample_repo
    with pytest.raises(ValueError, match="not found"):
        impact_engine.analyze_symbol_impact(repo_id, "non_existent_symbol_123")
