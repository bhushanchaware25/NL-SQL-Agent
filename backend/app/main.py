"""
NL2SQL Agent — FastAPI Application Entry Point
"""
from __future__ import annotations

import structlog
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import router
from app.memory.chroma_store import get_store
from app.db.connector import build_engine, validate_connection

log = structlog.get_logger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown hooks."""
    log.info("NL2SQL Agent starting up...")

    # Initialize ChromaDB (seeds examples if empty)
    store = get_store()
    log.info("ChromaDB ready", examples=store.count())

    # Validate default database connection
    try:
        engine = build_engine()
        if validate_connection(engine):
            log.info("Default database connected")
        else:
            log.warning("Default database not reachable — check DATABASE_URL")
    except Exception as exc:
        log.warning("Database check failed", error=str(exc))

    yield

    log.info("NL2SQL Agent shutting down...")


# ── App factory ───────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title="NL2SQL Agent API",
        description=(
            "AI-powered natural language to SQL conversion. "
            "Query any relational database using plain English."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(router)

    return app


app = create_app()


# ── Dev runner ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower(),
    )
