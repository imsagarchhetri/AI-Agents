import pytest
from models import AgentState
from graph import build_graph
from guardrails import calculate_risk_score, validate_rbac, redact_pii

def test_policy_qa_flow():
    graph = build_graph()
    state = AgentState(request_id="QA-01", user_query="What is the remote equipment stipend?", status="new")
    result = graph.invoke(state)
    assert result.status == "policy_qa"
    assert result.policy_context is not None

def test_risk_routing():
    assert calculate_risk_score("engineering", "senior_software_engineer", ["aws_console"]) >= 0.7
    assert calculate_risk_score("sales", "junior_rep", ["email"]) < 0.7

def test_rbac_denial():
    allowed, msg = validate_rbac("junior_accountant", "aws_console")
    assert allowed is False
    assert "RBAC_DENIED" in msg

def test_pii_redaction():
    assert "[EMAIL_REDACTED]" in redact_pii("Contact john.doe@company.com")