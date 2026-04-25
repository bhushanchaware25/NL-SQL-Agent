"""
Database connector utilities.

Provides:
- Engine factory (supports both sync and async engines)
- Schema reflection helper used by the Schema Inspector agent
- Connection validation
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import sqlalchemy as sa
from sqlalchemy import text, inspect as sa_inspect
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError

from app.core.config import settings


# ── Engine factory ────────────────────────────────────────────────────────────

def build_engine(database_url: Optional[str] = None) -> Engine:
    """
    Build a synchronous SQLAlchemy engine.

    Args:
        database_url: Override the default DATABASE_URL from settings.
                      Used when the user supplies an external database URL.

    Returns:
        A connected SQLAlchemy Engine.

    Raises:
        ValueError: If the URL is empty or malformed.
        OperationalError: If the database cannot be reached.
    """
    url = database_url or settings.database_url
    if not url:
        raise ValueError("database_url must not be empty")

    engine = sa.create_engine(
        url,
        pool_pre_ping=True,          # validate connection on checkout
        pool_size=5,
        max_overflow=10,
        connect_args={"connect_timeout": 10} if "postgresql" in url else {},
    )
    return engine


def validate_connection(engine: Engine) -> bool:
    """Return True if the engine can reach the database."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except OperationalError:
        return False


# ── Schema reflection ─────────────────────────────────────────────────────────

def reflect_schema(engine: Engine) -> Dict[str, Any]:
    """
    Reflect all tables, columns, primary keys, and foreign keys.

    Returns a dict structured as:
        {
          "tables": {
            "table_name": {
              "columns": [{"name": str, "type": str, "nullable": bool, "pk": bool}],
              "foreign_keys": [{"column": str, "references": "other_table.col"}]
            }
          }
        }
    """
    inspector = sa_inspect(engine)
    schema_info: Dict[str, Any] = {"tables": {}}

    for table_name in inspector.get_table_names():
        columns = []
        pk_cols = set(inspector.get_pk_constraint(table_name).get("constrained_columns", []))

        for col in inspector.get_columns(table_name):
            columns.append(
                {
                    "name": col["name"],
                    "type": str(col["type"]),
                    "nullable": col.get("nullable", True),
                    "pk": col["name"] in pk_cols,
                }
            )

        fks = []
        for fk in inspector.get_foreign_keys(table_name):
            for local_col, ref_col in zip(
                fk["constrained_columns"], fk["referred_columns"]
            ):
                fks.append(
                    {
                        "column": local_col,
                        "references": f"{fk['referred_table']}.{ref_col}",
                    }
                )

        schema_info["tables"][table_name] = {
            "columns": columns,
            "foreign_keys": fks,
        }

    return schema_info


def format_schema_for_prompt(schema_info: Dict[str, Any]) -> str:
    """
    Convert the reflected schema dict into a compact, LLM-readable string.

    Example output:
        Table: orders
          - id (INTEGER, PK)
          - customer_id (INTEGER, FK → customers.id)
          - total (NUMERIC)
          - created_at (TIMESTAMP)
    """
    lines: List[str] = []
    for table_name, table_data in schema_info["tables"].items():
        lines.append(f"Table: {table_name}")
        fk_map = {fk["column"]: fk["references"] for fk in table_data["foreign_keys"]}
        for col in table_data["columns"]:
            tags = []
            if col["pk"]:
                tags.append("PK")
            if col["name"] in fk_map:
                tags.append(f"FK → {fk_map[col['name']]}")
            if not col["nullable"] and not col["pk"]:
                tags.append("NOT NULL")
            tag_str = f"  ({', '.join(tags)})" if tags else ""
            lines.append(f"  - {col['name']} ({col['type']}{tag_str})")
        lines.append("")
    return "\n".join(lines)


def execute_query(engine: Engine, sql: str) -> List[Dict[str, Any]]:
    """
    Execute a SELECT query and return results as a list of row dicts.

    Args:
        engine: SQLAlchemy engine to use.
        sql: The SQL string to execute (already safety-checked).

    Returns:
        List of dicts where keys are column names.

    Raises:
        Exception: Any database error is propagated to the caller.
    """
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        keys = list(result.keys())
        rows = [dict(zip(keys, row)) for row in result.fetchmany(500)]
    return rows
