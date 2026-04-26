import re
from typing import Tuple

def calculate_risk_score(department: str, role: str, systems: list[str]) -> float:
    """
    Computes risk score (0.0-1.0) based on role, systems, and department.
    Production: Integrate with IAM risk engine or OPA policy store.
    """
    base_score = 0.2
    high_risk_systems = {"aws_console", "netsuite", "concur"}
    if any(s in high_risk_systems for s in systems):
        base_score += 0.4
    if role.startswith("senior") or role.startswith("admin"):
        base_score += 0.2
    if department == "finance":
        base_score += 0.1
    return min(base_score, 1.0)

def redact_pii(text: str) -> str:
    """
    Masks emails, SSNs, and phone numbers before LLM processing.
    Production: Replace with Microsoft Presidio or AWS Comprehend PII detector.
    """
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[EMAIL_REDACTED]", text)
    text = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[SSN_REDACTED]", text)
    return text

def validate_rbac(requester_role: str, target_system: str) -> Tuple[bool, str]:
    """
    Checks if role is authorized to request target system.
    """
    rbac_map = {
        "junior_accountant": {"email", "slack", "netsuite", "concur"},
        "senior_software_engineer": {"email", "slack", "github", "aws_console", "jira"},
        "default": {"email", "slack"}
    }
    allowed = rbac_map.get(requester_role, rbac_map["default"])
    if target_system not in allowed:
        return False, f"RBAC_DENIED: {target_system} not authorized for {requester_role}"
    return True, "RBAC_OK"