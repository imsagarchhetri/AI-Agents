import pytest
from models import AgentState
from graph import build_graph
from data_loader import load_tickets

def test_kb_resolve_flow():
    graph = build_graph()
    state = AgentState(
        ticket_id="INC-TEST-01",
        raw_description="Cannot connect to office WiFi. Authentication failed.",
        status="new"
    )
    result = graph.invoke(state)
    assert result["status"] in ["resolved", "needs_approval"]
    assert "kb_context" in result or "diagnostic_result" in result

def test_invalid_ticket():
    with pytest.raises(Exception):
        load_tickets("nonexistent.json")