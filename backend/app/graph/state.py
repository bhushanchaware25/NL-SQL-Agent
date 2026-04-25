"""
LangGraph shared state model for the NL2SQL agent pipeline.

Every node in the pipeline reads from and writes to this TypedDict.
LangGraph merges updates automatically between nodes.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    # ── Input ─────────────────────────────────────────────────────────────────
    question: str                          # User's natural language question
    database_url: Optional[str]            # Override DB URL (external DB support)

    # ── Schema Inspector output ───────────────────────────────────────────────
    schema_raw: Dict[str, Any]             # Full reflected schema dict
    schema_prompt: str                     # Compact schema string for LLM prompts

    # ── SQL Generator output ──────────────────────────────────────────────────
    few_shot_examples: List[Dict[str, str]]  # Retrieved ChromaDB examples
    sql: str                               # Generated SQL statement
    sql_explanation: str                   # LLM's explanation of the SQL

    # ── SQL Executor output ───────────────────────────────────────────────────
    execution_result: Optional[List[Dict[str, Any]]]  # Query result rows
    execution_error: Optional[str]         # DB error message (if any)

    # ── Critic/Validator output ───────────────────────────────────────────────
    is_valid: bool                         # Did the query satisfy the question?
    critique: str                          # Critic's reasoning
    suggested_fix: Optional[str]          # Critic's suggested SQL fix hint

    # ── Retry control ─────────────────────────────────────────────────────────
    retry_count: int                       # Number of retries so far

    # ── Response Synthesizer output ───────────────────────────────────────────
    answer: str                            # Final natural language answer
    chart_type: Optional[str]             # "bar" | "line" | "pie" | None
    chart_data: Optional[List[Dict[str, Any]]]  # Recharts-formatted data

    # ── Streaming trace ───────────────────────────────────────────────────────
    stream_events: List[Dict[str, Any]]    # Ordered list of agent step events
