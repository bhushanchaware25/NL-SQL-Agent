"""
Agent 2 — SQL Generator

Uses the reflected schema + few-shot ChromaDB examples + user question
to generate a valid, safe SQL SELECT query via the LLM.
"""
from __future__ import annotations

from typing import Optional

import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.core.llm import get_llm
from app.memory.chroma_store import get_store
from app.safety.sql_guard import check_sql_safety
from app.graph.state import AgentState

log = structlog.get_logger(__name__)


# ── Structured output schema ──────────────────────────────────────────────────

class SQLOutput(BaseModel):
    sql: str = Field(description="The complete SQL SELECT statement.")
    explanation: str = Field(description="A brief explanation of what this SQL does.")


# ── System prompt template ────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are an expert SQL engineer. Your job is to convert a natural language question
into a single, correct SQL SELECT query for a PostgreSQL database.

Rules:
1. Only generate SELECT statements — never INSERT, UPDATE, DELETE, DROP, or any DDL.
2. Use proper PostgreSQL syntax (ILIKE for case-insensitive text search, date_trunc for dates, etc.).
3. Always alias aggregated columns with meaningful names (e.g., AS total_revenue).
4. Limit results to 500 rows maximum using LIMIT unless the user asks for all rows.
5. Use table aliases when joining multiple tables for clarity.
6. If you are unsure, generate the most reasonable interpretation of the question.

{critique_instruction}
"""

FEW_SHOT_TEMPLATE = """\
## Database Schema
{schema}

## Similar Past Examples (use as reference)
{few_shots}

## User Question
{question}

Respond with a JSON object matching this schema:
{{
  "sql": "<complete SQL statement>",
  "explanation": "<brief explanation>"
}}
"""


def sql_generator_node(state: AgentState) -> AgentState:
    """
    LangGraph node: SQL Generator (Agent 2).

    Reads:  state.question, state.schema_prompt, state.critique (on retry),
            state.suggested_fix (on retry), state.retry_count
    Writes: state.sql, state.sql_explanation, state.few_shot_examples, state.stream_events
    """
    log.info("sql_generator: starting", retry=state.get("retry_count", 0))

    events = list(state.get("stream_events", []))
    retry_count = state.get("retry_count", 0)

    # Build critique instruction for retry context
    critique_instruction = ""
    if retry_count > 0 and state.get("critique"):
        critique_instruction = (
            f"\n## Previous Attempt Feedback (Retry #{retry_count})\n"
            f"The previous SQL was rejected for this reason:\n{state['critique']}\n"
        )
        if state.get("suggested_fix"):
            critique_instruction += f"Suggested fix: {state['suggested_fix']}\n"
        critique_instruction += "Please correct the SQL based on this feedback.\n"

    events.append(
        {
            "agent": "SQL Generator",
            "status": "running",
            "message": "Retrieving similar examples and generating SQL..." if retry_count == 0
                       else f"Rewriting SQL (attempt {retry_count + 1})...",
        }
    )

    # ── Retrieve few-shot examples ────────────────────────────────────────────
    store = get_store()
    few_shots = store.retrieve_similar(state["question"], k=3)
    few_shot_text = _format_few_shots(few_shots)

    # ── Build prompt ──────────────────────────────────────────────────────────
    system_msg = SystemMessage(
        content=SYSTEM_PROMPT.format(critique_instruction=critique_instruction)
    )
    human_msg = HumanMessage(
        content=FEW_SHOT_TEMPLATE.format(
            schema=state.get("schema_prompt", ""),
            few_shots=few_shot_text,
            question=state["question"],
        )
    )

    # ── Call LLM with structured output ──────────────────────────────────────
    llm = get_llm()
    structured_llm = llm.with_structured_output(SQLOutput)

    try:
        output = structured_llm.invoke([system_msg, human_msg])

        # openrouter/auto sometimes returns a raw dict instead of the Pydantic model
        if isinstance(output, dict):
            sql = output.get("sql", "").strip().rstrip(";") + ";"
            explanation = output.get("explanation", "")
        else:
            sql = output.sql.strip().rstrip(";") + ";"
            explanation = output.explanation

        if not sql or sql == ";":
            raise ValueError("LLM returned an empty SQL query.")

        # Safety check on generated SQL
        is_safe, reason = check_sql_safety(sql)
        if not is_safe:
            log.warning("sql_generator: safety block", reason=reason)
            raise ValueError(f"Generated SQL failed safety check: {reason}")

        log.info("sql_generator: done", sql_preview=sql[:80])
        events.append(
            {
                "agent": "SQL Generator",
                "status": "done",
                "message": f"SQL generated: {explanation}",
                "data": {"sql": sql, "explanation": explanation},
            }
        )

        return {
            **state,
            "sql": sql,
            "sql_explanation": explanation,
            "few_shot_examples": few_shots,
            "stream_events": events,
        }

    except Exception as exc:
        log.error("sql_generator: failed", error=str(exc))
        events.append(
            {
                "agent": "SQL Generator",
                "status": "error",
                "message": str(exc),
            }
        )
        raise RuntimeError(f"SQL Generator failed: {exc}") from exc


# ── Helpers ───────────────────────────────────────────────────────────────────

def _format_few_shots(examples: list) -> str:
    if not examples:
        return "No similar examples found."
    parts = []
    for i, ex in enumerate(examples, 1):
        parts.append(f"Example {i}:\n  Q: {ex['question']}\n  SQL: {ex['sql']}")
    return "\n\n".join(parts)
