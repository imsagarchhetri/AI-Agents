from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    """Centralized configuration with environment override support."""
    
    # LLM Configuration
    openai_api_key: Optional[str] = None
    llm_model: str = "gpt-4o-mini"
    router_model: str = "gpt-3.5-turbo"  # Faster/cheaper for classification
    temperature: float = 0.0
    max_tokens: int = 800

    # Production Constraints
    max_retries: int = 3
    retry_backoff_base: float = 2.0
    sla_warning_minutes: int = 60
    hitl_timeout_minutes: int = 30

    # External Systems
    servicenow_base_url: str = "https://dev12345.service-now.com/api/now/table"
    servicenow_user: Optional[str] = None
    servicenow_pass: Optional[str] = None

    # Observability
    langsmith_api_key: Optional[str] = None
    langsmith_tracing: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()