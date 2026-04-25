"""
Agent 3 — SQL Executor

Executes the generated SQL against the target database and stores results.
On error, captures the exception message for the Critic to analyze.
"""
from __future__ import annotations

import structlog

from app.db.connector import build_engine, execute_query
from app.graph.state import AgentState

log = structlog.get_logger(__name__)


def sql_executor_node(state: AgentState) -> AgentState:
    """
    LangGraph node: SQL Executor (Agent 3).

    Reads:  state.sql, state.database_url
    Writes: state.execution_result, state.execution_error, state.stream_events
    """
    log.info("sql_executor: starting", sql_preview=state.get("sql", "")[:80])

    events = list(state.get("stream_events", []))
    events.append(
        {
            "agent": "SQL Executor",
            "status": "running",
            "message": "Executing SQL query against the database...",
            "data": {"sql": state.get("sql", "")},
        }
    )

    try:
        db_url = state.get("database_url") or None
        engine = build_engine(db_url)
        rows = execute_query(engine, state["sql"])

        log.info("sql_executor: success", row_count=len(rows))
        events.append(
            {
                "agent": "SQL Executor",
                "status": "done",
                "message": f"Query returned {len(rows)} row(s).",
                "data": {"row_count": len(rows)},
            }
        )

        return {
            **state,
            "execution_result": rows,
            "execution_error": None,
            "is_valid": True,   # optimistic — Critic will validate
            "stream_events": events,
        }

    except Exception as exc:
        error_msg = str(exc)
        log.warning("sql_executor: query failed", error=error_msg)
        events.append(
            {
                "agent": "SQL Executor",
                "status": "error",
                "message": f"Query failed: {error_msg}",
            }
        )

        return {
            **state,
            "execution_result": None,
            "execution_error": error_msg,
            "is_valid": False,
            "stream_events": events,
        }
