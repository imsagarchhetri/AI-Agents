from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Centralized configuration with environment variable overrides."""

    openai_api_key: str = ""
    router_model: str = "gpt-4o-mini"
    temperature: float = 0.0
    max_tokens: int = 1000
    
    # RAG & Memory
    rag_index_path: str = "data/index"
    redis_url: str = "redis://localhost:6379/0"
    
    # Security & Compliance
    max_provisioning_retries: int = 2
    hitl_risk_threshold: float = 0.75  # Risk score above this requires approval
    allowed_systems: list[str] = ["email", "slack", "github", "aws_console", "jira", "netsuite", "concur"]
    
    # Observability
    langsmith_api_key: Optional[str] = None
    enable_tracing: bool = True
    
    class Config:
        env_file = ".env"

settings = Settings()
