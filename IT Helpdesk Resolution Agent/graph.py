from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from models import AgentState
from tools import search_kb, run_diagnostics, update_ticket
from router import route_ticket
from config import settings

# Initialize executor LLM
executor_llm = ChatOpenAI(model=settings.llm_model, temperature=0.0)

def classify_node(state: AgentState) -> dict:
    """Extracts category/priority, then routes."""
    # Simple rule-based extraction (production: NER model or regex)
    text = state.raw_description.lower()
    if any(kw in text for kw in ["wifi", "internet", "network", "vpn"]):
        category = "network"
    elif any(kw in text for kw in ["software", "app", "license", "excel"]):
        category = "software"
    elif any(kw in text for kw in ["hardware", "printer", "mouse", "monitor"]):
        category = "hardware"
    else:
        category = "unknown"
    priority = next((p for p in ["critical", "high", "medium", "low"] if p in text), "medium")

    return {
        "category": category,
        "priority": priority,
        "status": "processing"
    }

def kb_node(state: AgentState) -> dict:
    """Retrieves KB context and generates resolution."""
    kb_result = search_kb.invoke({"query": state.raw_description, "category": state.category})
    if kb_result == "NO_MATCH":
        return {"kb_context": None, "status": "needs_approval"}

    prompt = f"""Based on this KB article, generate a resolution plan for the ticket.
    KB:\n{kb_result}
    Ticket: {state.raw_description}
    Return ONLY the resolution steps."""

    plan = executor_llm.invoke([HumanMessage(content=prompt)]).content
    return {"kb_context": kb_result, "resolution_plan": plan, "status": "processing"}

def diagnose_node(state: AgentState) -> dict:
    """Runs diagnostics and updates state."""
    cmd = f"ping internal-dns && ipconfig /flushdns"
    result = run_diagnostics.invoke({"command": cmd})
    return {"diagnostic_result": result}

def resolve_node(state: AgentState) -> dict:
    """Generates final notes and updates ticket."""
    notes = state.resolution_plan or state.diagnostic_result or "Resolved via automated workflow."
    update_ticket.invoke({"ticket_id": state.ticket_id, "status": "resolved", "notes": notes})
    return {"status": "resolved"}

def hitl_node(state: AgentState) -> dict:
    """Simulates human approval wait. Production: Slack/Teams webhook."""
    return {"status": "needs_approval", "hitl_approval": None}

def check_approval(state: AgentState) -> str:
    """Conditional edge for HITL."""
    return "resolved" if state.hitl_approval else "escalated"

def build_graph() -> StateGraph:
    """ Compile the LangGraph state machine with conditional routing"""

    workflow = StateGraph(AgentState)
    workflow.add_node("classify", classify_node)
    workflow.add_node("kb_lookup", kb_node)
    workflow.add_node("diagnose", diagnose_node)
    workflow.add_node("hitl", hitl_node)
    workflow.add_node("resolve", resolve_node)

    workflow.set_entry_point("classify")
    workflow.add_conditional_edges(
        "classify",
        lambda s: route_ticket(s),
        {
            "kb_resolve": "kb_lookup",
            "diagnose": "diagnose",
            "hitl": "hitl",
            "escalate": END,
        }
    )
    workflow.add_edge("kb_lookup", "resolve")
    workflow.add_edge("diagnose", "resolve")
    workflow.add_conditional_edges("hitl", check_approval, {"resolved": "resolve", "escalated": END})
    workflow.add_edge("resolve", END)

    return workflow.compile()







