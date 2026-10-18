import os
import re
import zipfile
import shutil
import uuid
import logging
from typing import List, Dict, Set, Tuple, Optional, Any
import httpx
from app.config import settings

logger = logging.getLogger("codeimpact.ingestion")

EXCLUDED_DIR_PATTERNS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "venv",
    ".venv",
    "env",
    ".env",
    "dist",
    "build",
    "egg-info",
    ".idea",
    ".vscode",
}

EXCLUDED_FILE_PATTERNS = {
    ".env",
    ".pem",
    ".key",
    ".secret",
    ".DS_Store",
    "Thumbs.db",
}

BINARY_EXTENSIONS = {
    ".pyc", ".pyo", ".pyd", ".exe", ".dll", ".so", ".dylib",
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".pdf",
    ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar",
    ".db", ".sqlite", ".sqlite3", ".bin", ".dat", ".pkl",
    ".woff", ".woff2", ".ttf", ".eot",
}

LANGUAGE_EXT_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".java": "java",
    ".rs": "rust",
    ".cpp": "cpp",
    ".c": "c",
    ".cs": "csharp",
    ".rb": "ruby",
    ".php": "php",
    ".html": "html",
    ".css": "css",
    ".json": "json",
    ".md": "markdown",
    ".yaml": "yaml",
    ".yml": "yaml",
}

class IngestionError(Exception):
    """Raised when repository ingestion or validation fails."""
    pass

class RepositoryIngestionService:
    """Handles safe ingestion, security validation, and filtering of repositories."""

    def __init__(self, storage_base_dir: Optional[str] = None):
        self.storage_base_dir = os.path.abspath(storage_base_dir or settings.temp_dir)
        os.makedirs(self.storage_base_dir, exist_ok=True)

    def generate_repo_id(self, name_hint: str = "repo") -> str:
        clean_hint = re.sub(r"[^a-zA-Z0-9_\-]", "_", name_hint)[:20]
        return f"{clean_hint}_{uuid.uuid4().hex[:8]}"

    def validate_github_url(self, url: str) -> Tuple[str, str]:
        """
        Validate GitHub repository URL format.
        Returns (owner, repo_name).
        """
        pattern = r"^https?://github\.com/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+?)(?:\.git)?/?$"
        match = re.match(pattern, url.strip())
        if not match:
            raise IngestionError(
                "Invalid GitHub URL. Must be in format: https://github.com/owner/repository"
            )
        owner, repo = match.groups()
        return owner, repo

    async def download_github_repo(self, url: str) -> Tuple[str, str]:
        """
        Download a public GitHub repository as a ZIP archive without git execution.
        Returns (repo_id, destination_directory).
        """
        owner, repo = self.validate_github_url(url)
        repo_id = self.generate_repo_id(repo)
        dest_dir = os.path.join(self.storage_base_dir, repo_id)
        os.makedirs(dest_dir, exist_ok=True)

        zip_url = f"https://api.github.com/repos/{owner}/{repo}/zipball/HEAD"
        headers = {
            "User-Agent": "CodeImpact-AI-Analyzer",
            "Accept": "application/vnd.github.v3+json",
        }

        zip_temp_path = os.path.join(self.storage_base_dir, f"{repo_id}.zip")
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                response = await client.get(zip_url, headers=headers)
                if response.status_code == 404:
                    raise IngestionError(f"Repository {owner}/{repo} not found or is private.")
                elif response.status_code == 403:
                    raise IngestionError("GitHub API rate limit exceeded or access forbidden.")
                elif response.status_code != 200:
                    raise IngestionError(f"Failed to download repository from GitHub (HTTP {response.status_code}).")

                # Enforce ZIP size limit
                max_bytes = settings.max_zip_size_mb * 1024 * 1024
                if len(response.content) > max_bytes:
                    raise IngestionError(f"Repository ZIP exceeds maximum size of {settings.max_zip_size_mb}MB.")

                with open(zip_temp_path, "wb") as f:
                    f.write(response.content)

            self.extract_and_validate_zip(zip_temp_path, dest_dir)
            return repo_id, dest_dir
        finally:
            if os.path.exists(zip_temp_path):
                os.remove(zip_temp_path)

    def extract_and_validate_zip(self, zip_path: str, extract_to: str) -> None:
        """
        Extract ZIP archive with strict security validation:
        - Prevents Zip Slip (path traversal / absolute paths)
        - Enforces file count limits
        - Enforces total uncompressed size limits
        """
        max_bytes = settings.max_file_size_mb * 1024 * 1024 * 10
        total_extracted_bytes = 0
        file_count = 0

        target_dir = os.path.abspath(extract_to)

        with zipfile.ZipFile(zip_path, "r") as zf:
            for member in zf.infolist():
                file_count += 1
                if file_count > settings.max_file_count:
                    raise IngestionError(
                        f"Archive contains more than {settings.max_file_count} files (limit exceeded)."
                    )

                # Security check: Zip Slip path traversal prevention
                filename = member.filename
                if os.path.isabs(filename) or filename.startswith("/") or filename.startswith("\\"):
                    raise IngestionError(f"Security violation: Archive contains absolute path '{filename}'")

                # Resolve intended destination path
                dest_path = os.path.abspath(os.path.join(target_dir, filename))
                if not dest_path.startswith(target_dir):
                    raise IngestionError(f"Security violation: Path traversal detected in '{filename}'")

                total_extracted_bytes += member.file_size
                if total_extracted_bytes > max_bytes:
                    raise IngestionError("Archive uncompressed size exceeds allowable security limits.")

            # Safe extraction
            zf.extractall(target_dir)

        # In case GitHub zipball wraps in a top-level directory like "owner-repo-commit/..."
        # flatten if single directory at root
        top_entries = os.listdir(target_dir)
        if len(top_entries) == 1:
            candidate = os.path.join(target_dir, top_entries[0])
            if os.path.isdir(candidate):
                for item in os.listdir(candidate):
                    shutil.move(os.path.join(candidate, item), target_dir)
                os.rmdir(candidate)

    def scan_repository(self, repo_dir: str) -> Dict[str, Any]:
        """
        Scan repository directory and categorize files into:
        - Python source files to parse
        - Unsupported language files
        - Ignored files
        """
        python_files: List[str] = []
        unsupported_files: Dict[str, List[str]] = {}
        ignored_files: List[str] = []
        total_file_count = 0

        for root, dirs, files in os.walk(repo_dir):
            # Exclude prohibited directories in-place
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIR_PATTERNS and not d.startswith(".")]

            for file in files:
                total_file_count += 1
                if total_file_count > settings.max_file_count:
                    break

                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, repo_dir).replace("\\", "/")

                # Exclude secrets and system files
                if file in EXCLUDED_FILE_PATTERNS or file.startswith("."):
                    ignored_files.append(rel_path)
                    continue

                _, ext = os.path.splitext(file.lower())

                if ext in BINARY_EXTENSIONS:
                    ignored_files.append(rel_path)
                    continue

                lang = LANGUAGE_EXT_MAP.get(ext)
                if lang == "python":
                    python_files.append(rel_path)
                elif lang:
                    unsupported_files.setdefault(lang, []).append(rel_path)
                else:
                    ignored_files.append(rel_path)

        return {
            "python_files": python_files,
            "unsupported_files": unsupported_files,
            "unsupported_summary": {lang: len(f_list) for lang, f_list in unsupported_files.items()},
            "ignored_count": len(ignored_files),
            "total_python_files": len(python_files),
        }

    def cleanup_repo(self, repo_id: str) -> None:
        """Clean up extracted temporary repo files."""
        dest_dir = os.path.join(self.storage_base_dir, repo_id)
        if os.path.exists(dest_dir):
            shutil.rmtree(dest_dir, ignore_errors=True)

ingestion_service = RepositoryIngestionService()
