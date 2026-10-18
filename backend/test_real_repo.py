
import asyncio
import os
import sys
import logging

# Add backend to path
sys.path.append(os.path.abspath("E:/Hackathon/Graph Hacks/backend"))

from app.core.ingestion import ingestion_service
from app.core.parser import PythonRepositoryParser
from app.core.graph_builder import graph_builder
from app.core.db import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("real_repo_test")

async def run_test():
    repo_url = "https://github.com/encode/httpx"
    print(f"--- Attempting to index real repository: {repo_url} ---")
    
    try:
        # 1. Download
        repo_id, repo_path = await ingestion_service.download_github_repo(repo_url)
        print(f"Downloaded to: {repo_path} (ID: {repo_id})")
        
        # 2. Scan
        scan = ingestion_service.scan_repository(repo_path)
        print(f"Scan result: {scan['total_python_files']} Python files found.")
        
        # 3. Parse
        parser = PythonRepositoryParser(repo_path)
        parsed_files = parser.parse_all(scan['python_files'])
        print(f"Parsed {len(parsed_files)} files.")
        
        # 4. Build Graph
        build_result = graph_builder.build_graph(
            repo_id=repo_id,
            repo_name="HTTPX",
            repo_path=repo_path,
            parsed_files=parsed_files
        )
        print(f"Graph Build Result: {build_result}")
        
        if build_result['total_relationships'] == 0:
            print("ERROR: No relationships created. Resolution logic failed for this repo.")
        else:
            print("SUCCESS: Graph built with relationships.")

    except Exception as e:
        logger.exception(f"Failed to index real repo: {e}")

if __name__ == "__main__":
    asyncio.run(run_test())
