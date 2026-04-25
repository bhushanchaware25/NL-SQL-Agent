"""
SQL Safety Guard.

Blocks any SQL statement containing destructive operations before it reaches
the database. Two-layer check:
  1. Fast regex pre-filter on the raw SQL string.
  2. sqlparse AST token walk for accurate keyword detection.

Blocked operations (configurable via SQL_SAFETY_ENABLED env var):
  DROP, DELETE, UPDATE, INSERT, ALTER, TRUNCATE, GRANT, REVOKE,
  CREATE, REPLACE, MERGE, EXECUTE, EXEC, CALL
"""
from __future__ import annotations

import re
from typing import Tuple

import sqlparse
from sqlparse.sql import Statement
from sqlparse.tokens import Keyword, DDL, DML

from app.core.config import settings

# ── Blocked keyword sets ──────────────────────────────────────────────────────

_BLOCKED_DML = {
    "DELETE", "UPDATE", "INSERT", "MERGE", "REPLACE",
}

_BLOCKED_DDL = {
    "DROP", "CREATE", "ALTER", "TRUNCATE", "RENAME",
}

_BLOCKED_DCL = {
    "GRANT", "REVOKE",
}

_BLOCKED_PROC = {
    "EXECUTE", "EXEC", "CALL",
}

_ALL_BLOCKED: set[str] = (
    _BLOCKED_DML | _BLOCKED_DDL | _BLOCKED_DCL | _BLOCKED_PROC
)

# Pre-compiled regex for fast pre-check (case-insensitive, word boundaries)
_BLOCKED_RE = re.compile(
    r"\b(" + "|".join(re.escape(kw) for kw in _ALL_BLOCKED) + r")\b",
    re.IGNORECASE,
)


# ── Public API ────────────────────────────────────────────────────────────────

def check_sql_safety(sql: str) -> Tuple[bool, str]:
    """
    Determine whether the given SQL statement is safe to execute.

    Args:
        sql: Raw SQL string (may be multi-statement separated by semicolons).

    Returns:
        (is_safe, reason)
        - is_safe: True if the SQL passes all safety checks.
        - reason: Human-readable explanation if blocked, empty string otherwise.

    Note:
        If SQL_SAFETY_ENABLED is False (dev override), always returns (True, "").
    """
    if not settings.sql_safety_enabled:
        return True, ""

    if not sql or not sql.strip():
        return False, "Empty SQL statement."

    # Layer 1 — fast regex pre-filter
    match = _BLOCKED_RE.search(sql)
    if match:
        keyword = match.group(1).upper()
        return False, (
            f"Blocked: '{keyword}' statements are not permitted. "
            "Only SELECT queries are allowed."
        )

    # Layer 2 — sqlparse AST walk for accuracy
    for statement in sqlparse.parse(sql):
        blocked_kw = _find_blocked_keyword(statement)
        if blocked_kw:
            return False, (
                f"Blocked: '{blocked_kw}' detected in parsed SQL. "
                "Only SELECT queries are allowed."
            )

    # Layer 3 — ensure at least one SELECT token exists
    has_select = _has_select_token(sql)
    if not has_select:
        return False, (
            "Blocked: Statement does not appear to be a SELECT query. "
            "Only SELECT queries are permitted."
        )

    return True, ""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _find_blocked_keyword(statement: Statement) -> str | None:
    """Walk tokens in a parsed statement and return the first blocked keyword."""
    for token in statement.flatten():
        if token.ttype in (Keyword, DDL, DML):
            val = token.normalized.upper()
            if val in _ALL_BLOCKED:
                return val
    return None


def _has_select_token(sql: str) -> bool:
    """Return True if the SQL contains a SELECT keyword."""
    return bool(re.search(r"\bSELECT\b", sql, re.IGNORECASE))


def assert_safe(sql: str) -> None:
    """
    Convenience wrapper that raises ValueError if SQL is unsafe.

    Use this in agent code where you want an exception-based API.
    """
    is_safe, reason = check_sql_safety(sql)
    if not is_safe:
        raise ValueError(f"SQL Safety Violation: {reason}")
