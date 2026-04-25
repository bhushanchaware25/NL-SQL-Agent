"""
LangGraph Pipeline — NL2SQL Agent

Wires all five agent nodes into a StateGraph with:
- Linear flow: Schema Inspector → SQL Generator → SQL Executor → Critic → Synthesizer
- Conditional retry edge: Critic → SQL Generator (if not valid AND retries remain)
- Terminal edge: Critic → Synthesizer (if valid OR max retries exhausted)
"""
from __future__ import annotations

from typing import Literal

import structlog
from langgraph.graph import StateGraph, END

from app.agents.schema_inspector import schema_inspector_node
from app.agents.sql_generator import sql_generator_node
from app.agents.sql_executor import sql_executor_node
from app.agents.critic_validator import critic_validator_node
from app.agents.response_synthesizer import response_synthesizer_node
from app.core.config import settings
from app.graph.state import AgentState

log = structlog.get_logger(__name__)


# ── Node names ────────────────────────────────────────────────────────────────
SCHEMA_INSPECTOR   = "schema_inspector"
SQL_GENERATOR      = "sql_generator"
SQL_EXECUTOR       = "sql_executor"
CRITIC_VALIDATOR   = "critic_validator"
RESPONSE_SYNTH     = "response_synthesizer"


# ── Conditional routing ───────────────────────────────────────────────────────

def should_retry(state: AgentState) -> Literal["retry", "synthesize"]:
    """
    Route from Critic node.
    - "retry"     → back to SQL Generator
    - "synthesize" → forward to Response Synthesizer
    """
    is_valid   = state.get("is_valid", False)
    retry_count = state.get("retry_count", 0)

    if not is_valid and retry_count <= settings.max_retries:
        log.info("pipeline: routing to retry", attempt=retry_count)
        return "retry"

    log.info("pipeline: routing to synthesizer", is_valid=is_valid, retries=retry_count)
    return "synthesize"


# ── Graph construction ────────────────────────────────────────────────────────

def build_pipeline() -> StateGraph:
    """Build and compile the LangGraph pipeline."""
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node(SCHEMA_INSPECTOR, schema_inspector_node)
    graph.add_node(SQL_GENERATOR,    sql_generator_node)
    graph.add_node(SQL_EXECUTOR,     sql_executor_node)
    graph.add_node(CRITIC_VALIDATOR, critic_validator_node)
    graph.add_node(RESPONSE_SYNTH,   response_synthesizer_node)

    # Set entry point
    graph.set_entry_point(SCHEMA_INSPECTOR)

    # Linear edges
    graph.add_edge(SCHEMA_INSPECTOR, SQL_GENERATOR)
    graph.add_edge(SQL_GENERATOR,    SQL_EXECUTOR)
    graph.add_edge(SQL_EXECUTOR,     CRITIC_VALIDATOR)

    # Conditional retry edge
    graph.add_conditional_edges(
        CRITIC_VALIDATOR,
        should_retry,
        {
            "retry":      SQL_GENERATOR,     # loop back for self-correction
            "synthesize": RESPONSE_SYNTH,    # proceed to answer
        },
    )

    # Terminal edge
    graph.add_edge(RESPONSE_SYNTH, END)

    return graph.compile()


# ── Module-level compiled pipeline ───────────────────────────────────────────
pipeline = build_pipeline()
