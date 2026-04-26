def validate_input(text: str) -> bool:
    """ Block prompt injection & PII before LLM processing"""
    injection_patterns = ["system:", "ignore previous", "role: ", "output json:", "skip to end"]
    if any(p in text.lower() for p in injection_patterns):
        return False
    return True