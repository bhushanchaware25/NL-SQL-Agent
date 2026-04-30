"""
Agent 5 — Response Synthesizer

Converts raw SQL results into:
1. A natural language answer for the user.
2. An optional chart recommendation (type + Recharts-formatted data)
   when the result set is numeric or time-series in nature.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple

import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.core.llm import get_llm
from app.graph.state import AgentState

log = structlog.get_logger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
MAX_ROWS_IN_PROMPT = 30   # Only send a subset to the LLM for answer generation


# ── Structured output ─────────────────────────────────────────────────────────

class SynthesizerOutput(BaseModel):
    answer: str = Field(
        description="A clear, friendly natural language answer to the user's question."
    )
    chart_type: Optional[str] = Field(
        default=None,
        description="Recommended chart type: 'bar', 'line', 'pie', or null if no chart.",
    )
    x_key: Optional[str] = Field(
        default=None,
        description="Column name to use as X axis (or pie label).",
    )
    y_key: Optional[str] = Field(
        default=None,
        description="Column name to use as Y axis (or pie value).",
    )


# ── Prompts ───────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a friendly data analyst assistant. You receive:
- A user's question
- The SQL that was executed
- The result rows

Your tasks:
1. Write a clear, concise natural language answer (2-4 sentences). Include key numbers.
2. Recommend a visualization if appropriate:
   - Use "bar" for comparisons across categories.
   - Use "line" for time-series or trends over time.
   - Use "pie" for showing proportions/percentages (max 8 slices).
   - Use null if the result has only 1 row, is non-numeric, or a chart would add no value.
3. Specify x_key and y_key (column names from the result) if you recommend a chart.

Respond with JSON matching this schema:
{
  "answer": "...",
  "chart_type": "bar" | "line" | "pie" | null,
  "x_key": "column_name" | null,
  "y_key": "column_name" | null
}
"""

HUMAN_TEMPLATE = """\
## User Question
{question}

## SQL Executed
{sql}

## Query Results ({row_count} total rows, showing up to {sample_count})
{result_json}

Respond with JSON.
"""


def response_synthesizer_node(state: AgentState) -> AgentState:
    """
    LangGraph node: Response Synthesizer (Agent 5).

    Reads:  state.question, state.sql, state.execution_result
    Writes: state.answer, state.chart_type, state.chart_data, state.stream_events
    """
    log.info("response_synthesizer: starting")

    events = list(state.get("stream_events", []))
    events.append(
        {
            "agent": "Response Synthesizer",
            "status": "running",
            "message": "Synthesizing natural language answer and chart recommendation...",
        }
    )

    rows = state.get("execution_result") or []
    sample_rows = rows[:MAX_ROWS_IN_PROMPT]

    try:
        result_json = json.dumps(sample_rows, indent=2, default=str)
    except Exception:
        result_json = str(sample_rows)

    system_msg = SystemMessage(content=SYSTEM_PROMPT)
    human_msg = HumanMessage(
        content=HUMAN_TEMPLATE.format(
            question=state["question"],
            sql=state.get("sql", ""),
            row_count=len(rows),
            sample_count=len(sample_rows),
            result_json=result_json,
        )
    )

    llm = get_llm()
    structured_llm = llm.with_structured_output(SynthesizerOutput)

    try:
        output = structured_llm.invoke([system_msg, human_msg])

        # openrouter/auto sometimes returns a raw dict instead of the Pydantic model
        if isinstance(output, dict):
            answer = output.get("answer", "")
            chart_type = output.get("chart_type")
            x_key = output.get("x_key")
            y_key = output.get("y_key")
        else:
            answer = output.answer
            chart_type = output.chart_type
            x_key = output.x_key
            y_key = output.y_key

        chart_data = None
        if chart_type and x_key and y_key:
            chart_data = _format_chart_data(rows, x_key, y_key, chart_type)
            if not chart_data:
                chart_type = None  # fallback: no data to chart

        log.info("response_synthesizer: done", chart_type=chart_type)
        events.append(
            {
                "agent": "Response Synthesizer",
                "status": "done",
                "message": "Answer ready.",
                "data": {
                    "answer_preview": answer[:100],
                    "chart_type": chart_type,
                },
            }
        )

        return {
            **state,
            "answer": answer,
            "chart_type": chart_type,
            "chart_data": chart_data,
            "stream_events": events,
        }

    except Exception as exc:
        log.error("response_synthesizer: failed", error=str(exc))
        # Graceful fallback — return raw rows as answer
        fallback_answer = _fallback_answer(state["question"], rows)
        events.append(
            {
                "agent": "Response Synthesizer",
                "status": "done",
                "message": f"LLM synthesis failed, using fallback answer.",
            }
        )
        return {
            **state,
            "answer": fallback_answer,
            "chart_type": None,
            "chart_data": None,
            "stream_events": events,
        }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _format_chart_data(
    rows: List[Dict[str, Any]],
    x_key: str,
    y_key: str,
    chart_type: str,
) -> Optional[List[Dict[str, Any]]]:
    """
    Format rows into Recharts-compatible data array.

    For bar/line: [{"name": x_val, y_key: y_val}, ...]
    For pie:      [{"name": x_val, "value": y_val}, ...]
    """
    if not rows:
        return None

    chart_data = []
    for row in rows[:100]:  # cap at 100 points
        x_val = row.get(x_key)
        y_val = row.get(y_key)
        if x_val is None or y_val is None:
            continue
        if chart_type == "pie":
            chart_data.append({"name": str(x_val), "value": _to_float(y_val)})
        else:
            chart_data.append({"name": str(x_val), y_key: _to_float(y_val)})

    return chart_data if chart_data else None


def _to_float(val: Any) -> float:
    """Convert a value to float, defaulting to 0.0 on failure."""
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


def _fallback_answer(question: str, rows: List[Dict]) -> str:
    if not rows:
        return f"The query for '{question}' returned no results."
    count = len(rows)
    return (
        f"The query returned {count} row(s). "
        f"Please see the results table below for details."
    )
