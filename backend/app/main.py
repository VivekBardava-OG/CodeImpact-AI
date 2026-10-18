import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import router
from app.core.db import db_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.debug else logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("codeimpact.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing CodeImpact AI Backend...")
    # Check DB connectivity
    health = db_manager.check_health()
    if health["connected"]:
        logger.info(f"FalkorDB connection confirmed at {settings.falkordb_host}:{settings.falkordb_port}")
    else:
        logger.warning(f"FalkorDB not reachable during startup: {health.get('error')}")
    yield
    logger.info("Shutting down CodeImpact AI Backend...")

app = FastAPI(
    title="CodeImpact AI API",
    description="FalkorDB-powered Codebase Change Impact Analysis Agent",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for local Vite development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
