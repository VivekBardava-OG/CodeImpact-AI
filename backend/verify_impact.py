
import os
import sys
import logging

# Add backend to path
sys.path.append(os.path.abspath("E:/Hackathon/Graph Hacks/backend"))

from app.core.ingestion import ingestion_service
from app.core.parser import PythonRepositoryParser
from app.core.graph_builder import graph_builder
from app.core.impact_engine import impact_engine
from app.core.db import db_manager

logging.basicConfig(level=logging.INFO)

def run_verification():
    repo_path = 'E:/Hackathon/Graph Hacks/backend/fixtures/synthetic_test_repo'
    repo_id = 'synthetic-test'
    repo_name = 'Synthetic Test Repo'

    print(f"--- Indexing Repository: {repo_name} ---")
    scan = ingestion_service.scan_repository(repo_path)
    parser = PythonRepositoryParser(repo_path)
    parsed_files = parser.parse_all(scan['python_files'])

    build_result = graph_builder.build_graph(
        repo_id=repo_id,
        repo_name=repo_name,
        repo_path=repo_path,
        parsed_files=parsed_files
    )
    print(f"Build Result: {build_result}")

    # Target: get_user (defined in database.py)
    # Expected:
    # Direct dependent: authenticate_user (auth.py)
    # Indirect dependent: login (main.py)
    # Affected Test: test_authenticate_user_success, test_authenticate_user_failure (tests/test_auth.py)

    get_user_id = None
    for pf in parsed_files.values():
        for sym in pf.symbols:
            if sym.name == 'get_user':
                get_user_id = f"{repo_id}:{sym.id}"
                break
        if get_user_id: break

    if not get_user_id:
        print("ERROR: Could not find symbol 'get_user'")
        return

    print(f"\n--- Analyzing Impact for 'get_user' (ID: {get_user_id}) ---")
    try:
        impact = impact_engine.analyze_symbol_impact(repo_id, get_user_id)
        
        direct = [d['name'] for d in impact['direct_dependents']]
        indirect = [d['name'] for d in impact['indirect_dependents']]
        tests = [t['name'] for t in impact['affected_tests']]

        print(f"Direct Dependents: {direct} (Expected: ['authenticate_user'])")
        print(f"Indirect Dependents: {indirect} (Expected: ['login'])")
        print(f"Affected Tests: {tests} (Expected: ['test_authenticate_user_success', 'test_authenticate_user_failure'])")

        # Verification
        assert 'authenticate_user' in direct, "Missing direct dependent: authenticate_user"
        assert 'login' in indirect, "Missing indirect dependent: login"
        assert any('test_authenticate_user' in t for t in tests), "Missing affected tests"
        
        print("\nSUCCESS: Impact analysis is CORRECT.")
    except Exception as e:
        print(f"ERROR during analysis: {e}")

if __name__ == '__main__':
    run_verification()
