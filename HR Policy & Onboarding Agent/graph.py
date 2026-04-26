from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from models import AgentState
from tools import provision_accounts, generate_checklist
from guardrails import calculate_risk_score, redact_pii, validate_rbac
from rag_engine import load_policies, build_query_engine
from config import settings

# Initialize components
query_engine = build_query_engine(load_policies())
llm = ChatOpenAI(model=settings.router_model, temperature=0.0)

def classify_intent_node(state: AgentState) -> dict:
    """Determines if request is policy QA or onboarding action."""
    if state.user_query and not state.requested_systems:
        return {"status": "policy_qa"}
    return {"status": "onboarding"}

def retrieve_policy_node(state: AgentState) -> dict:
    """Retrieves versioned policy context & generates compliant response."""
    safe_query = redact_pii(state.user_query)
    response = query_engine.query(safe_query)
    
    # Enforce policy citation & block hallucination
    if "POLICY_NOT_FOUND" in str(response):
        return {"policy_context": None, "status": "needs_human_clarification"}
    return {"policy_context": str(response), "policy_version_cited": response.metadata.get("version", "unknown")}

def checklist_node(state: AgentState) -> dict:
    """Generates deterministic checklist based on role/department."""
    items = generate_checklist.invoke({
        "department": state.department,
        "role": state.role,
        "location": state.location
    }).split(" | ")
    return {"checklist_items": items}

def risk_node(state: AgentState) -> dict:
    """Calculates provisioning risk score for HITL routing."""
    score = calculate_risk_score(state.department, state.role, state.requested_systems)
    return {"risk_score": score, "status": "needs_approval" if score >= settings.hitl_risk_threshold else "provisioning"}

def check_approval(state: AgentState) -> str:
    """Conditional routing based on risk threshold."""
    return "provisioning" if state.risk_score < settings.hitl_risk_threshold else "needs_approval"

def hitl_node(state: AgentState) -> dict:
    """Simulates manager/HR approval step."""
    # Production: Slack/Teams interactive button or HRIS approval queue
    return {"status": "needs_approval", "approver_id": None}

def provisioning_node(state: AgentState) -> dict:
    """Validate RBAC & provision accounts."""
    valid_systems = []
    for sys in state.requested_systems:
        allowed, msg = validate_rbac(state.role, sys)
        if allowed:
            valid_systems.append(sys)
        else:
            state.error_log.append(msg)
    
    if not valid_systems:
        return {"status": "blocked", "error_log": state.error_log}

    result = provision_accounts.invoke({
        "systems": valid_systems,
        "email": state.employee_email,
        "request_id": state.request_id
    })
    return {"provisioned_accounts": valid_systems, "status": "completed"} 

def build_graph():
    """Compiles HR onboarding state machine with compliance routing."""
    workflow = StateGraph(AgentState)

    # --- Nodes ---
    workflow.add_node("intent_classification", classify_intent_node)
    workflow.add_node("retrieve_policy", retrieve_policy_node)
    workflow.add_node("generate_checklist", checklist_node)
    workflow.add_node("calculate_risk", risk_node)
    workflow.add_node("provisioning", provisioning_node)
    workflow.add_node("hitl", hitl_node)

    # --- Edges ---
    # Initial routing based on query type
    workflow.set_entry_point("intent_classification")
    workflow.add_conditional_edges("intent_classification", lambda s: s.status, {"policy_qa": "retrieve_policy", "onboarding": "generate_checklist"})
    workflow.add_edge("retrieve_policy", END)
    workflow.add_edge("generate_checklist", "calculate_risk")
    workflow.add_conditional_edges("calculate_risk", check_approval, {"needs_approval": "hitl", "provisioning": "provisioning"})        
    workflow.add_edge("hitl", "provisioning")
    workflow.add_edge("provisioning", END)
    
    return workflow.compile()
    