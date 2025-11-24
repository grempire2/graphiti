from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str = Field(default="ollama")
    groq_api_key: str | None = None
    gemini_api_key: str | None = None
    neo4j_uri: str = Field(default="bolt://localhost:7687")
    neo4j_user: str  # from env
    neo4j_password: str  # from env
    semaphore_limit: int = Field(default=15)  # graphiti default is 20
    ollama_base_url: str = Field(
        default="http://host.docker.internal:11434/v1",
    )
    ollama_embedding_base_url: str | None = Field(default=None)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings():
    return Settings()  # type: ignore[call-arg]


SettingsDep = Annotated[Settings, Depends(get_settings)]
