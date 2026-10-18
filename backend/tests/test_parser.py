import os
import pytest
from app.core.parser import PythonRepositoryParser

FIXTURE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "fixtures", "sample_project")
)

def test_parser_extracts_files_and_symbols():
    parser = PythonRepositoryParser(FIXTURE_DIR)
    files = [
        "auth/security.py",
        "services/user_service.py",
        "api/auth_controller.py",
        "tests/test_auth.py",
    ]
    parsed = parser.parse_all(files)
    
    assert "auth/security.py" in parsed
    sec = parsed["auth/security.py"]
    symbol_names = [s.name for s in sec.symbols]
    assert "authenticate_user" in symbol_names
    assert "hash_password" in symbol_names
    assert "verify_password" in symbol_names
    assert "create_access_token" in symbol_names

def test_parser_resolves_cross_file_calls():
    parser = PythonRepositoryParser(FIXTURE_DIR)
    files = [
        "auth/security.py",
        "services/user_service.py",
        "api/auth_controller.py",
        "tests/test_auth.py",
    ]
    parsed = parser.parse_all(files)
    
    # In services/user_service.py, login_user calls authenticate_user
    user_service = parsed["services/user_service.py"]
    login_user_sym = next(s for s in user_service.symbols if s.name == "login_user")
    
    auth_calls = [c for c in login_user_sym.calls if c.callee_name == "authenticate_user"]
    assert len(auth_calls) >= 1
    call = auth_calls[0]
    assert call.unresolved is False
    assert call.resolved_symbol_id == "auth/security.py:authenticate_user"

def test_parser_identifies_tests_and_test_calls():
    parser = PythonRepositoryParser(FIXTURE_DIR)
    files = ["auth/security.py", "tests/test_auth.py"]
    parsed = parser.parse_all(files)

    test_file = parsed["tests/test_auth.py"]
    assert test_file.is_test_file is True
    
    test_sym = next(s for s in test_file.symbols if s.name == "test_authenticate_user_success")
    assert test_sym.is_test is True
    
    call = next(c for c in test_sym.calls if c.callee_name == "authenticate_user")
    assert call.resolved_symbol_id == "auth/security.py:authenticate_user"

def test_parser_handles_syntax_errors_gracefully(tmp_path):
    bad_file = tmp_path / "broken.py"
    bad_file.write_text("def broken_syntax( {", encoding="utf-8")
    
    parser = PythonRepositoryParser(str(tmp_path))
    parsed = parser.parse_file("broken.py", str(bad_file))
    assert parsed.syntax_error is not None
    assert "SyntaxError" in parsed.syntax_error
