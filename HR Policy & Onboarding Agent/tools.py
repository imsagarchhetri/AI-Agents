import hashlib
from typing import Dict, List, Any
from langchain_core.tools import tool
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from models import AgentState
from config import settings

def _calculate_idempotency_hash(request_id: str, system: str) -> str:
    """Generates deterministic hash to prevent duplicate provisioning."""
    raw = f"{request_id}:{system}:{settings.openai_api_key[:8]}"  # Salted hash
    return hashlib.sha256(raw.encode()).hexdigest()[:16]

@retry(
    stop=stop_after_attempt(settings.max_provisioning_retries),
    wait=wait_exponential(multiplier=2),
    retry=retry_if_exception_type(Exception),
    reraise=True
)
def _provision_system_api(system: str, email: str, idempotency_key: str) -> Dict[str, Any]:
    """
    Simulates HRIS/IdP API call.
    Production: Use Okta SCIM, Microsoft Graph, or AWS SSO SDK with mutual TLS.
    """
    # Simulate network flakiness for retry logic
    if system == "aws_console" and idempotency_key.startswith("fail"):
        raise ConnectionError("Simulated AWS SSO timeout")
    return {"system": system, "email": email, "status": "provisioned", "idempotency_key": idempotency_key}

@tool
def provision_accounts(systems: List[str], email: str, request_id: str) -> str:
    """
    Provisions user accounts in requested systems with idempotency & RBAC checks.
    """
    results = []
    for sys in systems:
        if sys not in settings.allowed_systems:
            results.append(f"BLOCKED: {sys} not in allowlist")
            continue
        key = _calculate_idempotency_hash(request_id, sys)
        try:
            resp = _provision_system_api(sys, email, key)
            results.append(f"PROVISIONED: {sys} | Key: {key}")
        except Exception as e:
            results.append(f"FAILED: {sys} | Error: {str(e)}")
    return " | ".join(results)

@tool
def generate_checklist(department: str, role: str, location: str) -> str:
    """
    Generates role-specific onboarding checklist using template logic.
    Production: Replace with LLM + structured schema validation + HR template DB.
    """
    base = ["Complete I-9 & W-4", "IT Security Training", "Manager 1:1 Intro"]
    dept_map = {
        "engineering": ["Dev Environment Setup", "Code Review Guidelines", "CI/CD Access"],
        "finance": ["SOX Compliance Training", "NetSuite Onboarding", "Expense Policy Review"],
        "sales": ["CRM Training", "Sales Playbook Access", "Quota Review"]
    }
    items = base + dept_map.get(department, ["General Compliance"])
    if location.startswith("remote"):
        items.append("Remote Equipment Stipend Request")
    return " | ".join(items)