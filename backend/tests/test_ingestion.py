import os
import zipfile
import pytest
from app.core.ingestion import ingestion_service, IngestionError

def test_github_url_validation():
    # Valid URLs
    owner, repo = ingestion_service.validate_github_url("https://github.com/fastapi/fastapi")
    assert owner == "fastapi"
    assert repo == "fastapi"

    owner, repo = ingestion_service.validate_github_url("https://github.com/psf/requests.git")
    assert owner == "psf"
    assert repo == "requests"

    # Invalid URLs
    with pytest.raises(IngestionError):
        ingestion_service.validate_github_url("https://malicious.com/owner/repo")

    with pytest.raises(IngestionError):
        ingestion_service.validate_github_url("ftp://github.com/test")

def test_zip_slip_security_prevention(tmp_path):
    malicious_zip = tmp_path / "evil.zip"
    with zipfile.ZipFile(malicious_zip, "w") as zf:
        zf.writestr("../../etc/passwd", "root:x:0:0:")

    target_dir = tmp_path / "extracted"
    os.makedirs(target_dir, exist_ok=True)

    with pytest.raises(IngestionError, match="Security violation"):
        ingestion_service.extract_and_validate_zip(str(malicious_zip), str(target_dir))

def test_unsupported_languages_categorization(tmp_path):
    # Create multi-language directory
    (tmp_path / "app.py").write_text("print('hello')", encoding="utf-8")
    (tmp_path / "script.js").write_text("console.log('hi')", encoding="utf-8")
    (tmp_path / "main.go").write_text("package main", encoding="utf-8")
    (tmp_path / "secret.env").write_text("SECRET=123", encoding="utf-8")

    scan = ingestion_service.scan_repository(str(tmp_path))
    assert "app.py" in scan["python_files"]
    assert "javascript" in scan["unsupported_files"]
    assert "go" in scan["unsupported_files"]
    assert "secret.env" not in scan["python_files"]
