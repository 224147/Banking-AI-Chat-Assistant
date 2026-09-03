"""Application configuration loaded via pydantic-settings. Fails fast on missing required values."""
from enum import Enum
from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, Enum):
    OPENAI = "openai"
    MOCK = "mock"


class EmbeddingModel(str, Enum):
    LOCAL_HASH = "local-hash"
    OPENAI = "openai"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", frozen=True
    )

    app_name: str = "Banking AI Chat Assistant"
    environment: str = "development"
    debug: bool = False

    # LLM
    llm_provider: LLMProvider = LLMProvider.MOCK
    llm_model: str = "gpt-4o-mini"
    llm_api_key: str | None = None
    llm_base_url: str = "https://api.openai.com/v1"
    llm_timeout_seconds: float = 30.0

    # RAG
    embedding_model: EmbeddingModel = EmbeddingModel.LOCAL_HASH
    similarity_threshold: float = 0.25
    top_k: int = 4
    chroma_persist_dir: str = "./data/chroma"

    # Event bus (required -> fail fast if not configured)
    rabbitmq_url: str
    rabbitmq_exchange: str = "banking.events"

    # Database (required -> fail fast if not configured)
    database_url: str

    # Security
    session_secret_key: str = "change-me-in-production"
    idempotency_ttl_seconds: int = 86400
    cors_allow_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]

    # Observability
    otel_enabled: bool = False
    otel_service_name: str = "banking-chat-assistant"
    otel_exporter_endpoint: str | None = None

    @model_validator(mode="after")
    def validate_llm_credentials(self) -> "Settings":
        if self.llm_provider == LLMProvider.OPENAI and not self.llm_api_key:
            raise ValueError("LLM_API_KEY is required when LLM_PROVIDER=openai")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
