from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    status: str
    connected: bool
    host: str
    port: int
    latency_ms: Optional[float] = None
    error: Optional[str] = None

class RepoRegisterRequest(BaseModel):
    source_type: str = Field(..., description="'sample', 'local', or 'github'")
    github_url: Optional[str] = None
    local_path: Optional[str] = None
    name: Optional[str] = None

class RepoRegisterResponse(BaseModel):
    repo_id: str
    name: str
    path: str
    total_python_files: int
    unsupported_languages: Dict[str, int] = {}
    is_sample: bool = False

class RepoIndexResponse(BaseModel):
    repo_id: str
    graph_name: str
    total_files: int
    total_symbols: int
    total_tests: int
    total_relationships: int
    resolved_calls: int
    unresolved_calls: int
    duration_seconds: float

class RepoStatusResponse(BaseModel):
    repo_id: str
    status: str
    total_files: int
    total_symbols: int
    total_tests: int
    total_relationships: int
    indexed_at: Optional[float] = None

class SymbolItem(BaseModel):
    id: str
    name: str
    qualified_name: str
    symbol_type: str
    file_path: str
    start_line: int
    end_line: int
    is_test: bool = False

class SymbolsListResponse(BaseModel):
    repo_id: str
    total_symbols: int
    symbols: List[SymbolItem]
    files: List[str]

class ImpactAnalyzeRequest(BaseModel):
    repo_id: str
    symbol_id: str
    max_hops: int = Field(default=5, ge=1, le=10)

class ImpactAnalyzeResponse(BaseModel):
    target: Dict[str, Any]
    blast_radius_risk: str
    risk_evidence: Optional[str] = None
    metrics: Dict[str, Any]
    direct_dependents: List[Dict[str, Any]]
    indirect_dependents: List[Dict[str, Any]]
    affected_tests: List[Dict[str, Any]]
    affected_files: List[Dict[str, Any]]
    high_impact_shared_modules: List[Dict[str, Any]]
    visualization: Dict[str, Any]
    explanation: str

class DiffAnalyzeRequest(BaseModel):
    repo_id: str
    diff_text: str

class DiffAnalyzeResponse(BaseModel):
    changed_files_count: int
    changed_files: List[str]
    changed_symbols_count: int
    changed_symbols: List[Dict[str, Any]]
    aggregate_affected_symbols_count: int
    aggregate_affected_symbols: List[Dict[str, Any]]
    aggregate_affected_tests_count: int
    aggregate_affected_tests: List[Dict[str, Any]]

class AskQuestionRequest(BaseModel):
    repo_id: str
    symbol_id: str
    question: str

class AskQuestionResponse(BaseModel):
    answer: str
    source: str
    model: str
    grounded_facts: Dict[str, Any]
