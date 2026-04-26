from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from config import settings
from models import AgentState

router_llm = ChatOpenAI(
    model = settings.router_model,
    temperature = 0.0
)

ROUTER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an IT ticket router. Classify the ticket into ONE route:
    - 'kb_resolve': Issue matches known KB, low risk, automated fix possible
    - 'diagnose': Needs network/system diagnostics before resolution
    - 'escalate': Missing info, high severity, policy violation, or hardware replacement
    - 'hitl': Requires human approval for action (password reset, license change, data access)
    
    Respond ONLY with the route name."""),
    ("human", "Ticket Category: {category}\nPriority: {priority}\nDescription: {description}")
])

def route_ticket(state: AgentState) -> str:
    """Deterministic routing using lightweight LLM + fallback rules."""
    if "wifi" in state.raw_description.lower() or "excel" in state.raw_description.lower() or "printer" in state.raw_description.lower():
        return "kb_resolve"
    try:
        chain = ROUTER_PROMPT | router_llm
        response = chain.invoke({
            "category": state.category or "unknown",
            "priority": state.priority or "medium",
            "description": state.raw_description[:500]
        }).content.strip().lower()

        allowed_routes = {'kb_resolve', 'diagnose', 'escalate', 'hitl'}
        return response if response in allowed_routes else "diagnose"
    except Exception:
        # Fallback to determinstic rules if LLM fails
        if any(kw in state.raw_description.lower() for kw in ["replace", "broken", "damage"]):
            return "escalate"
        if state.category == "network":
            return "kb_resolve"
        return "diagnose"       

    
      

        

