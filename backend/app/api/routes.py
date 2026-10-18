import os
import time
import json
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from app.config import settings
from app.core.db import db_manager
from app.core.ingestion import ingestion_service, IngestionError
from app.core.parser import PythonRepositoryParser
from app.core.graph_builder import graph_builder
from app.core.impact_engine import impact_engine
from app.core.diff_analyzer import diff_analyzer
from app.core.llm_explainer import explainer_service
from app.api.schemas import (
    HealthResponse,
    RepoRegisterRequest,
    RepoRegisterResponse,
    RepoIndexResponse,
    RepoStatusResponse,
    SymbolsListResponse,
    SymbolItem,
    ImpactAnalyzeRequest,
    ImpactAnalyzeResponse,
    DiffAnalyzeRequest,
    DiffAnalyzeResponse,
    AskQuestionRequest,
    AskQuestionResponse,
)

logger = logging.getLogger("codeimpact.routes")
router = APIRouter(prefix="/api", tags=["CodeImpact AI"])

# --- PERSISTENCE LAYER ---
STORAGE_FILE = os.path.abspath("repositories.json")

def load_repositories() -> Dict[str, Any]:
    if os.path.exists(STORAGE_FILE):
        try:
            with open(STORAGE_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load repositories from file: {e}")
            return {}
    return {}

def save_repositories(repos: Dict[str, Any]):
    try:
        with open(STORAGE_FILE, "w") as f:
            json.dump(repos, f, indent=4)
    except Exception as e:
        logger.error(f"Failed to save repositories to file: {e}")

# Initialize REPOSITORIES from storage
REPOSITORIES: Dict[str, Dict[str, Any]] = load_repositories()

# Pre-register sample project fixture
SAMPLE_PROJECT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "fixtures", "sample_project")
)
if os.path.exists(SAMPLE_PROJECT_PATH):
    REPOSITORIES["sample-auth-service"] = {
        "repo_id": "sample-auth-service",
        "name": "Sample Auth & Payments Service",
        "path": SAMPLE_PROJECT_PATH,
        "is_sample": True,
        "status": "ready_to_index",
        "scan_meta": None,
        "parsed_files": None,
        "index_meta": None,
    }
    save_repositories(REPOSITORIES)

@router.get("/health", response_model=HealthResponse)
def get_health():
    res = db_manager.check_health()
    return HealthResponse(
        status=res["status"],
        connected=res["connected"],
        host=res["host"],
        port=res["port"],
        latency_ms=res.get("latency_ms"),
        error=res.get("error"),
    )

@router.get("/repositories")
def list_repositories():
    return list(REPOSITORIES.values())

@router.post("/repositories", response_model=RepoRegisterResponse)
async def register_repository(req: RepoRegisterRequest):
    try:
        if req.source_type == "sample":
            repo_id = "sample-auth-service"
            repo_path = SAMPLE_PROJECT_PATH
            repo_name = "Sample Auth & Payments Service"
            is_sample = True
        elif req.source_type == "github":
            if not req.github_url:
                raise HTTPException(status_code=400, detail="github_url is required for source_type='github'")
            repo_id, repo_path = await ingestion_service.download_github_repo(req.github_url)
            repo_name = req.name or os.path.basename(repo_path)
            is_sample = False
        elif req.source_type == "local":
            if not req.local_path or not os.path.isdir(req.local_path):
                raise HTTPException(status_code=400, detail="Invalid local directory path.")
            repo_path = os.path.abspath(req.local_path)
            repo_id = ingestion_service.generate_repo_id(req.name or os.path.basename(repo_path))
            repo_name = req.name or os.path.basename(repo_path)
            is_sample = False
        else:
            raise HTTPException(status_code=400, detail="Unsupported source_type.")

        scan = ingestion_service.scan_repository(repo_path)
        REPOSITORIES[repo_id] = {
            "repo_id": repo_id,
            "name": repo_name,
            "path": repo_path,
            "is_sample": is_sample,
            "status": "registered",
            "scan_meta": scan,
            "parsed_files": None,
            "index_meta": None,
        }
        save_repositories(REPOSITORIES)

        return RepoRegisterResponse(
            repo_id=repo_id,
            name=repo_name,
            path=repo_path,
            total_python_files=scan["total_python_files"],
            unsupported_languages=scan["unsupported_summary"],
            is_sample=is_sample,
        )
    except IngestionError as ie:
        raise HTTPException(status_code=400, detail=str(ie))
    except Exception as e:
        logger.error(f"Error registering repository: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/repositories/upload", response_model=RepoRegisterResponse)
async def upload_repository_zip(
    file: UploadFile = File(...),
    name: str = Form(None),
):
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip archives are supported.")

    repo_id = ingestion_service.generate_repo_id(name or file.filename.replace(".zip", ""))
    dest_dir = os.path.join(ingestion_service.storage_base_dir, repo_id)
    os.makedirs(dest_dir, exist_ok=True)
    temp_zip = os.path.join(ingestion_service.storage_base_dir, f"{repo_id}.zip")

    try:
        max_bytes = settings.max_zip_size_mb * 1024 * 1024
        size = 0
        with open(temp_zip, "wb") as f:
            while chunk := await file.read(1024 * 64):
                size += len(chunk)
                if size > max_bytes:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Uploaded ZIP exceeds maximum size limit of {settings.max_zip_size_mb}MB.",
                    )
                f.write(chunk)

        ingestion_service.extract_and_validate_zip(temp_zip, dest_dir)
        scan = ingestion_service.scan_repository(dest_dir)

        repo_name = name or file.filename.replace(".zip", "")
        REPOSITORIES[repo_id] = {
            "repo_id": repo_id,
            "name": repo_name,
            "path": dest_dir,
            "is_sample": False,
            "status": "registered",
            "scan_meta": scan,
            "parsed_files": None,
            "index_meta": None,
        }
        save_repositories(REPOSITORIES)

        return RepoRegisterResponse(
            repo_id=repo_id,
            name=repo_name,
            path=dest_dir,
            total_python_files=scan["total_python_files"],
            unsupported_languages=scan["unsupported_summary"],
            is_sample=False,
        )
    except IngestionError as ie:
        raise HTTPException(status_code=400, detail=str(ie))
    finally:
        if os.path.exists(temp_zip):
            os.remove(temp_zip)

@router.post("/repositories/{repo_id}/index", response_model=RepoIndexResponse)
def index_repository(repo_id: str):
    if repo_id not in REPOSITORIES:
        raise HTTPException(status_code=404, detail=f"Repository '{repo_id}' not found.")

    repo = REPOSITORIES[repo_id]
    start_time = time.perf_counter()

    scan = ingestion_service.scan_repository(repo["path"])
    parser = PythonRepositoryParser(repo["path"])
    parsed_files = parser.parse_all(scan["python_files"])

    build_result = graph_builder.build_graph(
        repo_id=repo_id,
        repo_name=repo["name"],
        repo_path=repo["path"],
        parsed_files=parsed_files,
    )

    duration = time.perf_counter() - start_time

    repo["status"] = "indexed"
    repo["parsed_files"] = parsed_files
    repo["index_meta"] = build_result
    save_repositories(REPOSITORIES)

    return RepoIndexResponse(
        repo_id=repo_id,
        graph_name=build_result["graph_name"],
        total_files=build_result["total_files"],
        total_symbols=build_result["total_symbols"],
        total_tests=build_result["total_tests"],
        total_relationships=build_result["total_relationships"],
        resolved_calls=build_result["resolved_calls"],
        unresolved_calls=build_result["unresolved_calls"],
        duration_seconds=round(duration, 3),
    )

@router.get("/repositories/{repo_id}/status", response_model=RepoStatusResponse)
def get_repository_status(repo_id: str):
    if repo_id not in REPOSITORIES:
        raise HTTPException(status_code=404, detail=f"Repository '{repo_id}' not found.")

    repo = REPOSITORIES[repo_id]
    graph_name = f"repo_{repo_id.replace('-', '_').replace('.', '_')}"

    try:
        counts_query = """
        MATCH (f:File) WITH count(f) as fc
        MATCH (s:Symbol) WITH fc, count(s) as sc
        MATCH (t:Test) WITH fc, sc, count(t) as tc
        MATCH ()-[r]->() WITH fc, sc, tc, count(r) as rc
        RETURN fc, sc, tc, rc
        """
        rows = db_manager.execute_query(graph_name, counts_query)
        if rows:
            fc, sc, tc, rc = rows[0]
            return RepoStatusResponse(
                repo_id=repo_id,
                status="indexed",
                total_files=fc,
                total_symbols=sc,
                total_tests=tc,
                total_relationships=rc,
                indexed_at=time.time(),
            )
    except Exception:
        pass

    meta = repo.get("index_meta") or {}
    return RepoStatusResponse(
        repo_id=repo_id,
        status=repo["status"],
        total_files=meta.get("total_files", 0),
        total_symbols=meta.get("total_symbols", 0),
        total_tests=meta.get("total_tests", 0),
        total_relationships=meta.get("total_relationships", 0),
        indexed_at=time.time(),
    )

@router.get("/repositories/{repo_id}/symbols", response_model=SymbolsListResponse)
def list_repository_symbols(repo_id: str):
    if repo_id not in REPOSITORIES:
        raise HTTPException(status_code=404, detail=f"Repository '{repo_id}' not found.")

    graph_name = f"repo_{repo_id.replace('-', '_').replace('.', '_')}"
    query = """
    MATCH (s:Symbol)
    RETURN s.id as id, s.name as name, s.qualified_name as qualified_name, s.symbol_type as symbol_type, s.file_path as file_path, s.start_line as start_line, s.end_line as end_line, false as is_test
    UNION ALL
    MATCH (t:Test)
    RETURN t.id as id, t.name as name, t.qualified_name as qualified_name, 'test' as symbol_type, t.file_path as file_path, t.start_line as start_line, t.end_line as end_line, true as is_test
    """
    try:
        rows = db_manager.execute_query(graph_name, query)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to query symbols from FalkorDB: {e}")

    symbols: List[SymbolItem] = []
    files_set = set()

    for r in rows:
        symbols.append(
            SymbolItem(
                id=r[0],
                name=r[1],
                qualified_name=r[2],
                symbol_type=r[3],
                file_path=r[4],
                start_line=r[5],
                end_line=r[6],
                is_test=r[7],
            )
        )
        files_set.add(r[4])

    return SymbolsListResponse(
        repo_id=repo_id,
        total_symbols=len(symbols),
        symbols=symbols,
        files=sorted(list(files_set)),
    )

@router.post("/impact/analyze", response_model=ImpactAnalyzeResponse)
def analyze_impact(req: ImpactAnalyzeRequest):
    if req.repo_id not in REPOSITORIES:
        raise HTTPException(status_code=404, detail=f"Repository '{req.repo_id}' not found.")

    try:
        impact = impact_engine.analyze_symbol_impact(
            repo_id=req.repo_id,
            symbol_id=req.symbol_id,
            max_hops=req.max_hops,
        )
        explanation = explainer_service.generate_deterministic_explanation(impact)
        impact["explanation"] = explanation
        return ImpactAnalyzeResponse(**impact)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"Error in impact analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/impact/diff", response_model=DiffAnalyzeResponse)
def analyze_diff(req: DiffAnalyzeRequest):
    if req.repo_id not in REPOSITORIES:
        raise HTTPException(status_code=404, detail=f"Repository '{req.repo_id}' not found.")

    try:
        result = diff_analyzer.analyze_diff(req.repo_id, req.diff_text)
        return DiffAnalyzeResponse(**result)
    except Exception as e:
        logger.error(f"Error analyzing diff: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/impact/ask", response_model=AskQuestionResponse)
async def ask_impact_question(req: AskQuestionRequest):
    if req.repo_id not in REPOSITORIES:
        raise HTTPException(status_code=404, detail=f"Repository '{req.repo_id}' not found.")

    try:
        impact = impact_engine.analyze_symbol_impact(req.repo_id, req.symbol_id)
        result = await explainer_service.answer_question(req.question, impact)
        return AskQuestionResponse(**result)
    except Exception as e:
        logger.error(f"Error answering impact question: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/repositories/{repo_id}/graph")
def get_full_graph(repo_id: str):
    if repo_id not in REPOSITORIES:
        raise HTTPException(status_code=404, detail=f"Repository '{repo_id}' not found.")

    graph_name = f"repo_{repo_id.replace('-', '_').replace('.', '_')}"
    nodes_query = """
    MATCH (n)
    WHERE n:Symbol OR n:Test OR n:File
    RETURN n.id, coalesce(n.name, n.path), labels(n), coalesce(n.symbol_type, 'file'), n.file_path
    """
    edges_query = """
    MATCH (s)-[r]->(t)
    WHERE (s:Symbol OR s:Test OR s:File) AND (t:Symbol OR t:Test OR t:File)
    RETURN s.id, t.id, type(r)
    """
    try:
        n_rows = db_manager.execute_query(graph_name, nodes_query)
        e_rows = db_manager.execute_query(graph_name, edges_query)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Graph retrieval failed: {e}")

    nodes = []
    edges = []
    for i, row in enumerate(n_rows):
        nid, name, labels, stype, fpath = row
        node_type = "testNode" if "Test" in labels else ("dependentNode" if "Symbol" in labels else "fileNode")
        nodes.append({
            "id": nid,
            "type": node_type,
            "data": {
                "label": name,
                "sublabel": fpath or "",
                "symbol_type": stype,
                "labels": labels,
            },
            "position": {"x": 100 + (i % 6) * 180, "y": 80 + (i // 6) * 120},
        })

    for j, erow in enumerate(e_rows):
        sid, tid, rtype = erow
        edges.append({
            "id": f"edge_{j}_{sid}->{tid}",
            "source": sid,
            "target": tid,
            "label": rtype,
            "animated": (rtype in ["CALLS", "TESTS"]),
        })

    return {"nodes": nodes, "edges": edges}

@router.get("/cypher/history")
def get_cypher_history(limit: int = 50):
    return db_manager.get_query_history(limit=limit)
