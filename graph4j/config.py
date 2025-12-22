from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str
    openai_base_url: str | None = None
    model_name: str | None = None
    embedding_model: str | None = None
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str

    # Fast embedder configuration (optional, defaults to main embedder if not set)
    fast_base_url: str | None = None
    fast_embedding_model: str | None = None

    # Fast database configuration (optional)
    neo4j_fast_uri: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def model_post_init(self, __context) -> None:
        """Set defaults for fast embedder and fast database if not explicitly configured.

        This ensures both embedders always have valid configurations.
        The fast embedder defaults to the main embedder settings if not specified.
        """
        # Fast embedding defaults to main configuration if not set
        # This allows the system to work even without explicit fast config
        if not self.fast_base_url:
            self.fast_base_url = self.openai_base_url
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
