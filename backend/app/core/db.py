import logging
import time
from typing import Any, Dict, List, Optional
from falkordb import FalkorDB
from app.config import settings

logger = logging.getLogger("codeimpact.db")

class CypherQueryRecord:
    def __init__(self, query: str, params: Optional[Dict[str, Any]], execution_time_ms: float, rows_returned: int):
        self.query = query
        self.params = params or {}
        self.execution_time_ms = execution_time_ms
        self.rows_returned = rows_returned
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "params": self.params,
            "execution_time_ms": round(self.execution_time_ms, 2),
            "rows_returned": self.rows_returned,
            "timestamp": self.timestamp,
        }

class FalkorDBClient:
    def __init__(self):
        self._client: Optional[FalkorDB] = None
        self._query_history: List[CypherQueryRecord] = []

    def get_client(self) -> FalkorDB:
        if self._client is None:
            logger.info(f"Connecting to FalkorDB at {settings.falkordb_host}:{settings.falkordb_port}...")
            self._client = FalkorDB(
                host=settings.falkordb_host,
                port=settings.falkordb_port,
                password=settings.falkordb_password,
            )
        return self._client

    def check_health(self) -> Dict[str, Any]:
        """Perform health check on FalkorDB instance."""
        try:
            client = self.get_client()
            g = client.select_graph("health_check_graph")
            start = time.perf_counter()
            g.query("RETURN 1 as ping")
            duration = (time.perf_counter() - start) * 1000
            return {
                "status": "healthy",
                "connected": True,
                "host": settings.falkordb_host,
                "port": settings.falkordb_port,
                "latency_ms": round(duration, 2),
            }
        except Exception as e:
            logger.error(f"FalkorDB health check failed: {e}")
            return {
                "status": "unhealthy",
                "connected": False,
                "host": settings.falkordb_host,
                "port": settings.falkordb_port,
                "error": str(e),
            }

    def get_graph(self, graph_name: str):
        """Retrieve a specific named graph."""
        client = self.get_client()
        return client.select_graph(graph_name)

    def execute_query(
        self,
        graph_name: str,
        query: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Any]:
        """
        Execute a Cypher query with timing and execution history recording.
        Supports parameterized queries.
        """
        g = self.get_graph(graph_name)
        start = time.perf_counter()
        try:
            if params:
                result = g.query(query, params)
            else:
                result = g.query(query)
            duration_ms = (time.perf_counter() - start) * 1000
            
            rows = result.result_set if hasattr(result, "result_set") else []
            record = CypherQueryRecord(query, params, duration_ms, len(rows))
            self._query_history.append(record)
            if len(self._query_history) > 100:
                self._query_history.pop(0)

            return rows
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.error(f"Error executing Cypher query on [{graph_name}]: {query} | Error: {e}")
            raise

    def get_query_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return recently executed Cypher queries with telemetry."""
        return [rec.to_dict() for rec in reversed(self._query_history[-limit:])]

    def clear_graph(self, graph_name: str) -> None:
        """Completely clear or delete a graph for clean re-indexing."""
        try:
            g = self.get_graph(graph_name)
            g.delete()
        except Exception as e:
            logger.warning(f"Could not delete graph {graph_name} (it may not exist): {e}")

db_manager = FalkorDBClient()
