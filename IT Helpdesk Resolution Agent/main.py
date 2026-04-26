from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import uvicorn

from guardrails import validate_input
from observability import run_agent
from data_loader import load_tickets, Ticket

app = FastAPI(title="IT Helpdesk Resolution Agent API")

class ProcessTicketRequest(BaseModel):
    ticket_id: str
    description: str

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/process_ticket")
def process_ticket(request: ProcessTicketRequest):
    # Validate input using guardrails
    if not validate_input(request.description):
        raise HTTPException(status_code=400, detail="Invalid input: Prompt injection or PII detected.")

    # Prepare ticket payload for the agent
    ticket_payload = {
        "ticket_id": request.ticket_id,
        "description": request.description
    }

    try:
        # Run the agent workflow
        result = run_agent(ticket_payload)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tickets/batch")
def process_batch(filepath: str = "data/it_tickets.json"):
    """Helper endpoint to process multiple tickets from a file."""
    tickets = load_tickets(filepath)
    results = []
    
    for ticket in tickets:
        if not validate_input(ticket.description):
            results.append({"ticket_id": ticket.ticket_id, "status": "failed", "reason": "guardrails"})
            continue
            
        ticket_payload = {
            "ticket_id": ticket.ticket_id,
            "description": ticket.description
        }
        try:
            res = run_agent(ticket_payload)
            results.append({"ticket_id": ticket.ticket_id, "status": "success", "result": res})
        except Exception as e:
            results.append({"ticket_id": ticket.ticket_id, "status": "failed", "reason": str(e)})
            
    return {"processed": len(tickets), "results": results}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
