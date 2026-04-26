import json
import os
from pydantic import BaseModel, Field, ValidationError, field_validator
from typing import List, Optional

class Ticket(BaseModel):
    """Pydantic model enforcing ServiceNow-compatible ticket schema."""
    ticket_id: str = Field(..., description="Unique incident ID, e.g., INC-2048")
    category: str = Field(..., description="Top-level category: network, software, hardware")
    subcategory: str = Field(..., description="Specific issue area")
    priority: str = Field(..., description="low, medium, high, critical")
    description: str = Field(..., min_length=5, max_length=2000)
    user_email: str = Field(..., description="Requester email for HITL notifications")
    status: str = Field(default="new", description="new, in_progress, resolved, escalated")
    created_at: str = Field(..., description="ISO 8601 timestamp")
    sla_deadline: str = Field(..., description="ISO 8601 deadline based on priority SLA")
    resolution_notes: str = Field(default="", description="Agent-generated or human resolution")

    @field_validator('priority')
    def validate_priority(cls, v:str) -> str:
        """Ensure priority is one of the allowed values."""
        allowed = {'low', 'medium', 'high', 'critical'}
        if v.lower() not in allowed:
            raise ValueError(f"Priority must be one of: {', '.join(allowed)}")
        return v.lower()

def load_tickets(filepath: str) -> List[Ticket]:
    """Load tickets from JSON file with validation.
    """
    try:
        with open(filepath,'r') as f:
            data = json.load(f)
        tickets = []
        for t in data:
            try:
                tickets.append(Ticket(**t))
            except ValidationError as e:
                print(f"Error validating ticket {t.get('ticket_id', 'Unknown')}: {e}")
        return tickets
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: File not found at {filepath}")