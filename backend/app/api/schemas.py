"""
Pydantic schemas for all API request and response bodies.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


# ── Request models ────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Natural language question about the database.",
        examples=["What are the top 5 products by revenue?"],
    )
    database_url: Optional[str] = Field(
        default=None,
        description=(
            "Optional external database URL. "
            "If omitted, the default demo database is used. "
            "Format: postgresql://user:password@host:port/dbname"
        ),
    )

    @model_validator(mode="after")
    def sanitize_question(self) -> "QueryRequest":
        self.question = self.question.strip()
        return self


class DBConnectionRequest(BaseModel):
    database_url: str = Field(
        ...,
        description="SQLAlchemy-compatible database URL to validate.",
        examples=["postgresql://user:password@localhost:5432/mydb"],
    )


# ── Response models ───────────────────────────────────────────────────────────

class StreamEvent(BaseModel):
    event: str                           # "agent_step" | "done" | "error"
    agent: Optional[str] = None
    status: Optional[str] = None         # "running" | "done" | "error" | "retry"
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class QueryResponse(BaseModel):
    question: str
    sql: str
    explanation: str
    answer: str
    rows: List[Dict[str, Any]]
    row_count: int
    chart_type: Optional[str] = None
    chart_data: Optional[List[Dict[str, Any]]] = None
    retry_count: int = 0
    stream_events: List[Dict[str, Any]] = Field(default_factory=list)


class SchemaResponse(BaseModel):
    tables: Dict[str, Any]
    table_count: int


class HealthResponse(BaseModel):
    status: str
    database: str
    few_shot_count: int


class DBConnectionResponse(BaseModel):
    connected: bool
    message: str
    table_count: Optional[int] = None


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
