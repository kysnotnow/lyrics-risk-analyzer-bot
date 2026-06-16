from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: SecretStr
    llm_api_key: SecretStr | None = None
    llm_base_url: str = "http://localhost:11434/v1"
    llm_model: str = "llama3.2"
    llm_timeout_seconds: float = 300.0
    llm_temperature: float = 0.1
    llm_json_mode_fallback: bool = True

    database_path: Path = Path("data/bot.db")
    log_level: str = "INFO"
    max_lyrics_length: int = Field(default=8000, ge=100)


@lru_cache
def get_settings() -> Settings:
    return Settings()
