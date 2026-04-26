from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, Any
from datetime import datetime, timezone

class AgentState(BaseModel):
    """LangGraph-compatible state schema. All fields are serializable."""

    ticket_id: str
    raw_description: str
    category: Optional[str] = None
    subcategory: Optional[str] = None
    priority: Optional[str] = None
    kb_context: Optional[str] = None
    diagnostic_result: Optional[str] = None
    resolution_plan: Optional[str] = None
    hitl_approval: Optional[bool] = None
    status: Literal["new", "processing", "needs_approval", "resolved", "escalated"] = "new"
    error_log: list[str] = Field(default_factory=list)
    trace_id: str = Field(default_factory=lambda: f"trace-{datetime.now(timezone.utc).isoformat()}")
    execution_cost_tokens: int = 0
