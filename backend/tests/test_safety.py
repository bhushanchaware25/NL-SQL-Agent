"""Tests for the SQL safety guard."""
import pytest
from app.safety.sql_guard import check_sql_safety, assert_safe


# ── Safe queries (should pass) ────────────────────────────────────────────────
@pytest.mark.parametrize("sql", [
    "SELECT * FROM orders;",
    "SELECT id, name FROM products WHERE price > 100;",
    "SELECT COUNT(*) FROM customers;",
    "SELECT p.name, SUM(oi.quantity) FROM products p JOIN order_items oi ON p.id=oi.product_id GROUP BY p.name;",
    "  select * from orders  ",   # leading whitespace
])
def test_safe_selects(sql):
    is_safe, reason = check_sql_safety(sql)
    assert is_safe, f"Expected safe but got: {reason}"


# ── Dangerous queries (should be blocked) ────────────────────────────────────
@pytest.mark.parametrize("sql,expected_kw", [
    ("DROP TABLE orders;",                   "DROP"),
    ("DELETE FROM customers WHERE id=1;",    "DELETE"),
    ("UPDATE products SET price=0;",         "UPDATE"),
    ("INSERT INTO products VALUES (1,'x');", "INSERT"),
    ("ALTER TABLE orders ADD COLUMN foo INT;","ALTER"),
    ("TRUNCATE TABLE reviews;",              "TRUNCATE"),
    ("GRANT ALL ON orders TO public;",       "GRANT"),
    ("REVOKE SELECT ON orders FROM user1;",  "REVOKE"),
    ("CREATE TABLE evil (x INT);",           "CREATE"),
    ("EXECUTE sp_something;",               "EXECUTE"),
])
def test_blocked_statements(sql, expected_kw):
    is_safe, reason = check_sql_safety(sql)
    assert not is_safe, f"Expected '{expected_kw}' to be blocked"
    assert expected_kw.lower() in reason.lower() or "blocked" in reason.lower()


# ── Edge cases ────────────────────────────────────────────────────────────────
def test_empty_sql():
    is_safe, reason = check_sql_safety("")
    assert not is_safe

def test_assert_safe_raises():
    with pytest.raises(ValueError, match="Safety Violation"):
        assert_safe("DROP TABLE orders;")

def test_assert_safe_passes():
    assert_safe("SELECT 1;")   # should not raise
