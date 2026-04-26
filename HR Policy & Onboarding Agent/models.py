from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, Any, List
from datetime import datetime

class AgentState(BaseModel):
    """LangGraph state schema for HR onboarding workflow."""
    request_id: str
    employee_email: str
    department: str
    role: str
    location: str
    requested_systems: List[str]
    user_query: Optional[str] = None  # Optional policy QA string
    policy_context: Optional[str] = None
    checklist_items: List[str] = Field(default_factory=list)
    provisioned_accounts: List[str] = Field(default_factory=list)
    risk_score: float = Field(default=0.0)
    status: Literal["new", "processing", "needs_approval", "approved", "provisioning", "completed", "blocked", "policy_qa", "onboarding"] = "new"
    error_log: List[str] = Field(default_factory=list)
    trace_id: str = Field(default_factory=lambda: f"hr-trace-{datetime.utcnow().isoformat()}")
    approver_id: Optional[str] = None
    policy_version_cited: Optional[str] = None