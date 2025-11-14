from typing import Literal

from graphiti_core import Graphiti
from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient
from graphiti_core.llm_client.config import LLMConfig

from app.client_factory import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    create_embedder_client,
    create_llm_client,
)
from app.config import SettingsDep


def create_graphiti_client(
    settings: SettingsDep,
    llm_client_type: Literal["groq", "gemini", "ollama"] = "groq",
    embedder_client_type: Literal["gemini", "ollama"] = "gemini",
) -> Graphiti:
    """
    Create a Graphiti client instance with the specified LLM and embedder clients.

    Args:
        settings: Application settings containing API keys
        llm_client_type: Type of LLM client to use (default: 'groq')
        embedder_client_type: Type of embedder client to use (default: 'gemini')

    Returns:
        A configured Graphiti client instance
    """
    # Get API keys from settings based on client types
    llm_api_key = None
    if llm_client_type == "groq":
        llm_api_key = settings.groq_api_key
    elif llm_client_type == "gemini":
        llm_api_key = settings.gemini_api_key

    embedder_api_key = None
    if embedder_client_type == "gemini":
        embedder_api_key = settings.gemini_api_key

    # Create LLM client
    llm_client = create_llm_client(llm_client_type, llm_api_key)

    # Create embedder client
    embedder = create_embedder_client(embedder_client_type, embedder_api_key)

    # Initialize cross-encoder with Ollama configuration
    # Using Ollama's OpenAI-compatible API endpoint
    cross_encoder_config = LLMConfig(
        api_key=settings.openai_api_key,
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
    )
    try:
        cross_encoder = OpenAIRerankerClient(config=cross_encoder_config)
    except Exception:
        # If initialization fails, set to None and let Graphiti handle it
        cross_encoder = None

    # Create Graphiti instance with custom clients
    client = Graphiti(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
        llm_client=llm_client,
        embedder=embedder,
        cross_encoder=cross_encoder,
        max_coroutines=settings.semaphore_limit,
    )

    return client
