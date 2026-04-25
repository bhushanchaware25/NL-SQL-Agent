"""
FastAPI routes — REST endpoints and WebSocket streaming.

Endpoints:
  GET  /health           — Liveness + readiness probe
  GET  /api/schema       — Return reflected schema of default (or custom) DB
  POST /api/db/connect   — Validate an external database connection
  POST /api/query        — Synchronous query (for testing / curl)
  WS   /ws/query         — WebSocket streaming query
"""
from __future__ import annotations

import json
from typing import Optional

import structlog
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import JSONResponse

from app.api.schemas import (
    QueryRequest, QueryResponse, SchemaResponse,
    HealthResponse, DBConnectionRequest, DBConnectionResponse, ErrorResponse,
)
from app.core.config import settings
from app.db.connector import build_engine, validate_connection, reflect_schema
from app.graph.pipeline import pipeline
from app.memory.chroma_store import get_store

log = structlog.get_logger(__name__)
router = APIRouter()


# ── Health ────────────────────────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse, tags=["system"])
def health_check():
    """Liveness + readiness probe."""
    # Check default DB
    try:
        engine = build_engine()
        db_status = "connected" if validate_connection(engine) else "unreachable"
    except Exception as exc:
        db_status = f"error: {exc}"

    return HealthResponse(
        status="ok",
        database=db_status,
        few_shot_count=get_store().count(),
    )


# ── Schema ────────────────────────────────────────────────────────────────────

@router.get("/api/schema", response_model=SchemaResponse, tags=["database"])
def get_schema(database_url: Optional[str] = Query(default=None)):
    """Reflect and return the database schema."""
    try:
        engine = build_engine(database_url)
        if not validate_connection(engine):
            raise HTTPException(status_code=503, detail="Cannot reach the database.")
        schema = reflect_schema(engine)
        return SchemaResponse(
            tables=schema["tables"],
            table_count=len(schema["tables"]),
        )
    except HTTPException:
        raise
    except Exception as exc:
        log.error("schema endpoint failed", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))


# ── DB Connection Validation ──────────────────────────────────────────────────

@router.post("/api/db/connect", response_model=DBConnectionResponse, tags=["database"])
def validate_db_connection(body: DBConnectionRequest):
    """
    Validate an external database connection URL.
    Returns connection status and table count.
    """
    try:
        engine = build_engine(body.database_url)
        is_connected = validate_connection(engine)
        if not is_connected:
            return DBConnectionResponse(
                connected=False,
                message="Could not connect to the database. Check credentials and network.",
            )
        schema = reflect_schema(engine)
        return DBConnectionResponse(
            connected=True,
            message=f"Connected successfully.",
            table_count=len(schema["tables"]),
        )
    except Exception as exc:
        log.warning("db connect validation failed", error=str(exc))
        return DBConnectionResponse(
            connected=False,
            message=f"Connection failed: {str(exc)}",
        )


# ── Synchronous Query ─────────────────────────────────────────────────────────

@router.post("/api/query", response_model=QueryResponse, tags=["query"])
def run_query(body: QueryRequest):
    """
    Execute a natural language query synchronously.
    Use the WebSocket endpoint for streaming in production.
    """
    log.info("sync_query", question=body.question)

    initial_state = {
        "question": body.question,
        "database_url": body.database_url,
        "retry_count": 0,
        "stream_events": [],
    }

    try:
        final_state = pipeline.invoke(initial_state)
    except Exception as exc:
        log.error("pipeline failed", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))

    rows = final_state.get("execution_result") or []
    return QueryResponse(
        question=body.question,
        sql=final_state.get("sql", ""),
        explanation=final_state.get("sql_explanation", ""),
        answer=final_state.get("answer", ""),
        rows=rows,
        row_count=len(rows),
        chart_type=final_state.get("chart_type"),
        chart_data=final_state.get("chart_data"),
        retry_count=final_state.get("retry_count", 0),
        stream_events=final_state.get("stream_events", []),
    )


# ── WebSocket Streaming Query ─────────────────────────────────────────────────

@router.websocket("/ws/query")
async def ws_query(websocket: WebSocket):
    """
    WebSocket endpoint for real-time streaming query execution.

    Protocol:
      CLIENT → { "question": str, "database_url": str | null }
      SERVER → { "event": "agent_step", "agent": str, "status": str, "message": str, "data": {...} }
      SERVER → { "event": "done", "answer": str, "sql": str, "chart_type": str|null,
                  "chart_data": [...], "rows": [...], "row_count": int }
      SERVER → { "event": "error", "message": str }
    """
    await websocket.accept()
    log.info("ws_query: client connected")

    try:
        # Receive initial message
        raw = await websocket.receive_text()
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            await _ws_error(websocket, "Invalid JSON payload.")
            return

        question = payload.get("question", "").strip()
        database_url = payload.get("database_url") or None

        if len(question) < 3:
            await _ws_error(websocket, "Question is too short (minimum 3 characters).")
            return

        log.info("ws_query: received question", question=question)

        initial_state = {
            "question": question,
            "database_url": database_url,
            "retry_count": 0,
            "stream_events": [],
        }

        # Stream pipeline steps
        last_event_count = 0
        final_state = None

        for step in pipeline.stream(initial_state, stream_mode="values"):
            final_state = step
            events = step.get("stream_events", [])

            # Only send newly added events
            new_events = events[last_event_count:]
            for event in new_events:
                await websocket.send_json(
                    {
                        "event": "agent_step",
                        "agent": event.get("agent"),
                        "status": event.get("status"),
                        "message": event.get("message"),
                        "data": event.get("data"),
                    }
                )
            last_event_count = len(events)

        # Send final done frame
        if final_state:
            rows = final_state.get("execution_result") or []
            await websocket.send_json(
                {
                    "event": "done",
                    "question": question,
                    "answer": final_state.get("answer", ""),
                    "sql": final_state.get("sql", ""),
                    "sql_explanation": final_state.get("sql_explanation", ""),
                    "chart_type": final_state.get("chart_type"),
                    "chart_data": final_state.get("chart_data"),
                    "rows": rows,
                    "row_count": len(rows),
                    "retry_count": final_state.get("retry_count", 0),
                }
            )
        else:
            await _ws_error(websocket, "Pipeline returned no result.")

    except WebSocketDisconnect:
        log.info("ws_query: client disconnected")
    except Exception as exc:
        log.error("ws_query: unhandled error", error=str(exc))
        try:
            await _ws_error(websocket, str(exc))
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _ws_error(websocket: WebSocket, message: str) -> None:
    try:
        await websocket.send_json({"event": "error", "message": message})
    except Exception:
        pass
