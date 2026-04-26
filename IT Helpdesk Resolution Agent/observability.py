import os
from langsmith import Client
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from graph import build_graph
from config import settings
from models import AgentState

resource = Resource.create({
    "service.name": "it-helpdesk-agent",
    "service.version": "1.0.0"
})
provider = TracerProvider(resource=resource)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

@tracer.start_as_current_span("agent_execution")
def run_agent(ticket: dict):
    """ Wraps graph execution with tracing & metrics. """

    graph = build_graph()
    initial_state = AgentState(
        ticket_id=ticket["ticket_id"],
        raw_description=ticket["description"],
        status = "new"
    )

    result = graph.invoke(initial_state)

    # Log to LangSmith if configured
    if settings.langsmith_tracing and settings.langsmith_api_key:
        client = Client(api_key=settings.langsmith_api_key)
        client.create_run(
            name=f"Ticket-{ticket['ticket_id']}",
            inputs={"description": ticket["description"]},
            outputs={"status": result.get("status"), "trace_id": result.get("trace_id")},
            run_type="chain"
        )
    return result
