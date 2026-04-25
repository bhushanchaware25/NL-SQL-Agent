"""
Agent 4 — Critic / Validator

Evaluates the SQL execution result and determines if it:
1. Successfully answered the user's question.
2. Contains sensible, non-empty results (unless zero rows is correct).
3. Does not appear malformed or logically incorrect.

If invalid, produces a critique + suggested fix to feed back into Agent 2.
"""
from __future__ import annotations

import json
import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.core.llm import get_llm
from app.core.config import settings
from app.graph.state import AgentState

log = structlog.get_logger(__name__)


# ── Structured output ─────────────────────────────────────────────────────────

class CriticOutput(BaseModel):
    is_valid: bool = Field(
        description="True if the SQL correctly answered the question."
    )
    critique: str = Field(
        description="Reasoning for the validation decision."
    )
    suggested_fix: str = Field(
        default="",
        description="Concrete hint for fixing the SQL if is_valid is False.",
    )


# ── Prompts ───────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a strict SQL quality validator. Given:
- A user's natural language question
- The SQL query that was executed
- The result rows returned (or an error message)

Evaluate whether the SQL CORRECTLY and COMPLETELY answered the question.

Validation criteria:
1. If there was a SQL syntax or execution error → is_valid = False.
2. If the result is empty AND empty is clearly wrong for the question → is_valid = False.
3. If the result rows make logical sense given the question → is_valid = True.
4. If the SQL is semantically wrong (wrong columns, wrong filters) → is_valid = False.
5. Empty results are VALID if the question is asking for something that genuinely has no matches.

When is_valid is False, provide a clear, actionable suggested_fix that the SQL Generator
can use to rewrite the query.

Respond with a JSON matching this schema:
{
  "is_valid": bool,
  "critique": "reasoning...",
  "suggested_fix": "concrete fix hint or empty string"
}
"""

HUMAN_TEMPLATE = """\
## User Question
{question}

## SQL Executed
{sql}

## Execution Result
{result_summary}

Evaluate and respond with JSON.
"""


def critic_validator_node(state: AgentState) -> AgentState:
    """
    LangGraph node: Critic / Validator (Agent 4).

    Reads:  state.question, state.sql, state.execution_result,
            state.execution_error, state.retry_count
    Writes: state.is_valid, state.critique, state.suggested_fix,
            state.retry_count, state.stream_events
    """
    retry_count = state.get("retry_count", 0)
    log.info("critic_validator: starting", retry=retry_count)

    events = list(state.get("stream_events", []))
    events.append(
        {
            "agent": "Critic / Validator",
            "status": "running",
            "message": "Validating query result quality...",
        }
    )

    # ── Fast-fail on execution error ──────────────────────────────────────────
    if state.get("execution_error"):
        critique = (
            f"SQL execution failed with error: {state['execution_error']}. "
            "The query must be corrected."
        )
        suggested_fix = (
            f"Fix the SQL to resolve this database error: {state['execution_error']}"
        )
        log.info("critic_validator: execution error → invalid", retry=retry_count)

        events.append(
            {
                "agent": "Critic / Validator",
                "status": "retry" if retry_count < settings.max_retries else "error",
                "message": f"Validation failed (execution error). "
                           f"{'Retrying...' if retry_count < settings.max_retries else 'Max retries reached.'}",
                "data": {"critique": critique},
            }
        )

        return {
            **state,
            "is_valid": False,
            "critique": critique,
            "suggested_fix": suggested_fix,
            "retry_count": retry_count + 1,
            "stream_events": events,
        }

    # ── LLM validation for successful execution ───────────────────────────────
    result = state.get("execution_result", []) or []
    result_summary = _summarize_result(result)

    system_msg = SystemMessage(content=SYSTEM_PROMPT)
    human_msg = HumanMessage(
        content=HUMAN_TEMPLATE.format(
            question=state["question"],
            sql=state.get("sql", ""),
            result_summary=result_summary,
        )
    )

    llm = get_llm()
    structured_llm = llm.with_structured_output(CriticOutput)

    try:
        output: CriticOutput = structured_llm.invoke([system_msg, human_msg])
        is_valid = output.is_valid
        critique = output.critique
        suggested_fix = output.suggested_fix or ""

        # On success, add good example to few-shot store
        if is_valid:
            try:
                from app.memory.chroma_store import get_store
                get_store().add_example(state["question"], state.get("sql", ""))
                log.info("critic_validator: added example to ChromaDB store")
            except Exception:
                pass  # Non-critical — don't fail the pipeline

        log.info("critic_validator: done", is_valid=is_valid)
        events.append(
            {
                "agent": "Critic / Validator",
                "status": "done" if is_valid else ("retry" if retry_count < settings.max_retries else "error"),
                "message": critique,
                "data": {
                    "is_valid": is_valid,
                    "suggested_fix": suggested_fix,
                },
            }
        )

        return {
            **state,
            "is_valid": is_valid,
            "critique": critique,
            "suggested_fix": suggested_fix,
            "retry_count": retry_count + (0 if is_valid else 1),
            "stream_events": events,
        }

    except Exception as exc:
        log.error("critic_validator: LLM call failed", error=str(exc))
        # If critic itself fails, optimistically pass through
        events.append(
            {
                "agent": "Critic / Validator",
                "status": "done",
                "message": f"Critic LLM failed ({exc}), passing through.",
            }
        )
        return {
            **state,
            "is_valid": True,
            "critique": "Critic validation skipped due to LLM error.",
            "suggested_fix": "",
            "stream_events": events,
        }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _summarize_result(rows: list) -> str:
    """Create a compact result summary for the critic prompt."""
    if not rows:
        return "The query returned 0 rows (empty result set)."

    count = len(rows)
    sample = rows[:5]
    try:
        sample_str = json.dumps(sample, indent=2, default=str)
    except Exception:
        sample_str = str(sample)

    return f"Returned {count} row(s). Sample (up to 5):\n{sample_str}"
