from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env.local"), env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Iowa Pork Compliance Copilot"
    environment: str = "development"
    database_url: str = "sqlite:///./copilot.sqlite3"
    openai_api_key: str = ""
    openai_chat_model: str = "gpt-5.6-terra"
    openai_embedding_model: str = "text-embedding-3-large"
    openai_embedding_dimensions: int = 1024
    openai_reasoning_effort: str = "low"
    cors_origins: str = "http://localhost:3000"
    admin_api_key: str = ""
    app_access_token: str = ""
    retrieval_limit: int = Field(default=8, ge=3, le=15)
    max_question_chars: int = Field(default=2000, ge=200, le=10000)

    @property
    def sqlalchemy_database_url(self) -> str:
        url = self.database_url
        if url.startswith("postgres://"):
            url = "postgresql+psycopg://" + url.removeprefix("postgres://")
        elif url.startswith("postgresql://"):
            url = "postgresql+psycopg://" + url.removeprefix("postgresql://")
        return url

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
