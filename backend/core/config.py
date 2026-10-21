"""Application configuration settings."""

import json
from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings loaded from environment or defaults."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General application configuration
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG: bool = True

    # Security policy and institutional domain
    ALLOWED_EMAIL_DOMAIN: str = "unsa.edu.pe"
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://inti.unsa.edu.pe",
    ]

    # Persistence credentials (Supabase)
    SUPABASE_URL: str = "https://xyzcompany.supabase.co"
    SUPABASE_ANON_KEY: str = "dummy_anon_key"
    SUPABASE_SERVICE_ROLE_KEY: str = "dummy_service_key"
    SUPABASE_JWT_SECRET: str = "super-secret-supabase-jwt-key-for-development-unsa-2026"

    # JWT generation parameters
    JWT_ALGORITHM: str = "HS256"
    JWT_AUDIENCE: str = "authenticated"
    JWT_ISSUER: str = "inti-auth-service"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # LLM and embedding configurations
    GROQ_API_KEY: str = "gsk_dummy"
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    OPENROUTER_API_KEY: str = "sk-or-dummy"
    OPENROUTER_MODEL: str = "deepseek/deepseek-chat"
    OPENAI_API_KEY: str = "sk-proj-dummy"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536

    # RAG parameters
    RAG_SIMILARITY_THRESHOLD: float = 0.75
    RAG_TOP_K: int = 5
    RAG_TEMPERATURE: float = 0.1

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, value: Union[str, List[str]]) -> List[str]:
        """Parse CORS_ORIGINS whether passed as list, JSON string, or comma-separated values."""
        if isinstance(value, str):
            value = value.strip()
            if value.startswith("[") and value.endswith("]"):
                try:
                    return json.loads(value)
                except Exception:
                    pass
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


settings = Settings()
