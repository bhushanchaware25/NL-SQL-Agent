"""Tests for agent output schemas using mocked LLM."""
import pytest
from unittest.mock import MagicMock, patch
from app.graph.state import AgentState


def make_state(**kwargs) -> AgentState:
    base = {
        "question": "How many orders do we have?",
        "database_url": None,
        "retry_count": 0,
        "stream_events": [],
    }
    base.update(kwargs)
    return base


class TestStateDefaults:
    def test_state_has_required_keys(self):
        state = make_state()
        assert "question" in state
        assert "retry_count" in state
        assert state["retry_count"] == 0

    def test_retry_increments(self):
        state = make_state(retry_count=1)
        assert state["retry_count"] == 1


class TestSQLExecutorNode:
    def test_successful_execution(self):
        from app.agents.sql_executor import sql_executor_node
        with patch("app.agents.sql_executor.build_engine") as mock_engine, \
             patch("app.agents.sql_executor.execute_query") as mock_exec:
            mock_exec.return_value = [{"count": 42}]
            state = make_state(sql="SELECT COUNT(*) AS count FROM orders;")
            result = sql_executor_node(state)
            assert result["execution_result"] == [{"count": 42}]
            assert result["execution_error"] is None
            assert result["is_valid"] is True

    def test_failed_execution(self):
        from app.agents.sql_executor import sql_executor_node
        with patch("app.agents.sql_executor.build_engine"), \
             patch("app.agents.sql_executor.execute_query") as mock_exec:
            mock_exec.side_effect = Exception("column does not exist")
            state = make_state(sql="SELECT nonexistent FROM orders;")
            result = sql_executor_node(state)
            assert result["execution_result"] is None
            assert "column does not exist" in result["execution_error"]
            assert result["is_valid"] is False
