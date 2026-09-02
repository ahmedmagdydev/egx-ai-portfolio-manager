from pathlib import Path

from fastapi import Request
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    postgres_user: str = "egx"
    postgres_password: str = "change_me"
    postgres_db: str = "egx"
    postgres_host: str = "127.0.0.1"
    postgres_port: int = 5432
    database_url: str = "postgresql+psycopg://egx:change_me@127.0.0.1:5432/egx"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    frontend_port: int = 3000
    log_level: str = "INFO"
    health_timeout_seconds: int = 2
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_reasoning_model: str = "qwen3.5:9b"
    ollama_embedding_model: str = "qwen3-embedding:4b-q4_K_M"
    next_public_api_base_url: str = "http://127.0.0.1:8000"

    def safe_database_target(self) -> str:
        return f"{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


settings = Settings()


def get_settings(request: Request) -> Settings:
    return request.app.state.settings
