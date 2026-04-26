import json

def load_onboarding_requests():
    """Load mock onboarding requests from JSON."""
    with open("data/onboarding_requests.json", "r") as f:
        return json.load(f)
