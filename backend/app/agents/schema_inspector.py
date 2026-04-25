"""
Agent 1 — Schema Inspector

Reflects the target database schema and formats it as a compact string
ready to be injected into LLM prompts.
"""
from __future__ import annotations

import structlog

from app.db.connector import build_engine, reflect_schema, format_schema_for_prompt, validate_connection
from app.graph.state import AgentState

log = structlog.get_logger(__name__)


def schema_inspector_node(state: AgentState) -> AgentState:
    """
    LangGraph node: Schema Inspector (Agent 1).

    Reads:  state.database_url (optional override)
    Writes: state.schema_raw, state.schema_prompt, state.stream_events
    """
    log.info("schema_inspector: starting")

    events = list(state.get("stream_events", []))
    events.append(
        {
            "agent": "Schema Inspector",
            "status": "running",
            "message": "Connecting to database and reflecting schema...",
        }
    )

    try:
        db_url = state.get("database_url") or None
        engine = build_engine(db_url)

        if not validate_connection(engine):
            raise ConnectionError("Cannot reach the database. Check your DATABASE_URL.")

        schema_raw = reflect_schema(engine)
        schema_prompt = format_schema_for_prompt(schema_raw)

        events.append(
            {
                "agent": "Schema Inspector",
                "status": "done",
                "message": f"Schema reflected: {len(schema_raw['tables'])} tables found.",
                "data": {"table_count": len(schema_raw["tables"])},
            }
        )
        log.info("schema_inspector: done", tables=len(schema_raw["tables"]))

        return {
            **state,
            "schema_raw": schema_raw,
            "schema_prompt": schema_prompt,
            "stream_events": events,
        }

    except Exception as exc:
        log.error("schema_inspector: failed", error=str(exc))
        events.append(
            {
                "agent": "Schema Inspector",
                "status": "error",
                "message": str(exc),
            }
        )
        raise RuntimeError(f"Schema Inspector failed: {exc}") from exc
