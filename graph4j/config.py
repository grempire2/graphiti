from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str
    openai_base_url: str | None = None
    model_name: str | None = None

    # Dedicated URL for quality embedding (optional, fallbacks to openai_base_url if not set)
    embedding_base_url: str | None = None
    embedding_model: str | None = None

    # Fast embedder configuration (optional, defaults to embedding_base_url if not set)
    fast_base_url: str | None = None
    fast_embedding_model: str | None = None

    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str

    # Fast database configuration (optional)
    neo4j_fast_uri: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def model_post_init(self, __context) -> None:
        """Set defaults for embedding URLs, fast embedder and fast database if not explicitly configured.

        This ensures all services have valid configurations even if only sparse settings are provided.
        """
        # Set defaults for embedding URL if not explicitly set
        if not self.embedding_base_url:
            self.embedding_base_url = self.openai_base_url

        # Fast embedding defaults to main embedding configuration if not set
        if not self.fast_base_url:
            self.fast_base_url = self.embedding_base_url
        if not self.fast_embedding_model:
            self.fast_embedding_model = self.embedding_model

        # Fast database defaults to port 7787 on localhost if not set
        # This assumes default neo4j_uri uses port 7687
        if not self.neo4j_fast_uri:
            self.neo4j_fast_uri = "bolt://localhost:7787"


@lru_cache
def get_settings():
    return Settings()  # type: ignore[call-arg]


SettingsDep = Annotated[Settings, Depends(get_settings)]
