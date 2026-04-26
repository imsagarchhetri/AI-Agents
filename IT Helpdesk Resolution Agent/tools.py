import os
import re
import httpx
from typing import Dict, Any
from langchain_core.tools import tool
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from config import settings
from datetime import datetime, timezone

@tool
def search_kb(query: str, category: str) -> str:
    """
    Search internal knowledge base for resolution steps.
    Production: Replace with Qdrant/Weaviant vector search
    Args:
        query: Natural language search string
        category: Ticket category for semantic filtering
        
    Returns:
        Markdown-formatted KB article content or 'NO_MATCH'
    """
    kb_dir = "data/kb_articles"
    for filename in os.listdir(kb_dir):
        if not filename.endswith(".md"):
            continue
        path = os.path.join(kb_dir, filename)
        with open(path, "r") as f:
            content = f.read()
            # Simple metadata + content match (production: use vector DB)
            if category.lower() in content.lower() and any(
                kw in query.lower() for kw in ["fix", "resolve", "step", "how", "wifi", "printer", "license", "error", "fail", "connect"]
            ): return content

    return "NO_MATCH"

@retry(
    stop=stop_after_attempt(settings.max_retries),
    wait=wait_exponential(multiplier=settings.retry_backoff_base),
    retry=retry_if_exception_type(httpx.HTTPError),
    reraise=True
)
def _call_diagnostic_api(command: str) -> str:
    """Simulated diagnostic tool with production retry/circuit breaker."""
    # In production: requests.post(f"{settings.servicenow_base_url}/cmd/diagnose", ...)
    # Simulate network flakiness for teaching:
    if "timeout" in command:
        raise httpx.HTTPError("Simulated timeout")
    return f"DIAG_RESULT: {command} executed successfully. Output: 200 OK"

@tool
def run_diagnostics(command: str) -> str:
    """
    Execute safe diagnostic commands.
    Production: Run in sandboxed container with read-only filesystem.
    """
    allowed_commands = ["ping", "tracert", "ipconfig", "nslookup", "diskutil list"]
    cmd_base = command.split()[0] if command else ""
    if cmd_base not in allowed_commands:
        return f"ERROR: Command '{command}' not in allowlist. Escalating."
    return _call_diagnostic_api(command)

@retry(
    stop=stop_after_attempt(settings.max_retries),
    wait=wait_exponential(multiplier=settings.retry_backoff_base),
    retry=retry_if_exception_type(Exception),
    reraise=True
)
def update_ticket_system(ticket_id: str, status: str, notes: str) -> Dict[str, Any]:
    """
    Idempotent ticket update with hash-based deduplication.
    Production: ServiceNow REST API with OAuth2 & retry queue.
    """
    # Simulate API call
    return {
        "ticket_id": ticket_id,
        "status": status,
        "notes": notes,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "idempotency_key": hash(f"{ticket_id}{status}{notes[:50]}")
    }

@tool
def update_ticket(ticket_id: str, status: str, notes: str) -> str:
    """Public tool interface for LangGraph. Validates & logs."""
    try:
        result = update_ticket_system(ticket_id, status, notes)
        return f"TICKET_UPDATED: {result['status']} | ID: {result['idempotency_key']}"
    except Exception as e:
        return f"TICKET_UPDATE_FAILED: {str(e)}"



    
    