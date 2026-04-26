from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from models import AgentState
from config import settings
from datetime import datetime

resource = Resource.create({"service.name": "hr-onboarding-agent", "compliance.framework": "SOC2"})
provider = TracerProvider(resource=resource)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

@tracer.start_as_current_span("hr_agent_execution")
def run_onboarding(request: dict, query: str = None):
    """Wraps graph execution with compliance tracing & metrics."""
    from graph import build_graph
    graph = build_graph()
    state = AgentState(
        request_id=request["request_id"],
        employee_email=request["employee_email"],
        department=request["department"],
        role=request["role"],
        location=request["location"],
        requested_systems=request["requested_systems"],
        user_query=query if query is not None else request.get("user_query"),
        status="new"
    )
    result = graph.invoke(state)
    
    # Audit log emission (production: async Kafka/S3)
    audit_entry = {
        "trace_id": result.get("trace_id"),
        "request_id": result.get("request_id"),
        "status": result.get("status"),
        "policy_version": result.get("policy_version_cited"),
        "risk_score": result.get("risk_score"),
        "provisioned": result.get("provisioned_accounts"),
        "timestamp": datetime.utcnow().isoformat()
    }
    print(f"[AUDIT] {audit_entry}")  # Replace with structured logger
    return result