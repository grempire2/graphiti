"""
Client factory for creating LLM and embedder clients with hardcoded model names.
"""

from graphiti_core.embedder.gemini import GeminiEmbedder, GeminiEmbedderConfig
from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.llm_client.gemini_client import GeminiClient
from graphiti_core.llm_client.groq_client import GroqClient
from graphiti_core.llm_client.openai_generic_client import OpenAIGenericClient

# Hardcoded model names
GROQ_MODEL = "openai/gpt-oss-120b"
GROQ_SMALL_MODEL = "openai/gpt-oss-20b"

GEMINI_MODEL = "gemini-flash-latest"
GEMINI_SMALL_MODEL = "gemini-flash-lite-latest"
GEMINI_EMBEDDING_MODEL = "gemini-embedding-001"

OLLAMA_MODEL = "qwen3:30b-a3b-instruct-2507-q4_K_M"
OLLAMA_SMALL_MODEL = "qwen3:30b-a3b-instruct-2507-q4_K_M"
OLLAMA_EMBEDDING_MODEL = "embeddinggemma"
OLLAMA_SEARCH_EMBEDDING_MODEL = (
    "hf.co/unsloth/embeddinggemma-300m-GGUF"  # Different model for search
)
OLLAMA_BASE_URL = "http://host.docker.internal:11434/v1"


def create_llm_client(
    client_type: str,
    api_key: str | None = None,
    base_url: str | None = None,
) -> GroqClient | GeminiClient | OpenAIGenericClient:
    """
    Create an LLM client with hardcoded model names.

    Args:
        client_type: Type of client to create ('groq', 'gemini', or 'ollama')
        api_key: API key for the client (required for groq and gemini, ignored for ollama)

    Returns:
        An LLM client instance configured with hardcoded model names
    """
    if client_type == "groq":
        if not api_key:
            raise ValueError("GROQ_API_KEY is required for Groq client")
        config = LLMConfig(
            api_key=api_key,
            model=GROQ_MODEL,
            small_model=GROQ_SMALL_MODEL,
        )
        return GroqClient(config=config)

    elif client_type == "gemini":
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required for Gemini client")
        config = LLMConfig(
            api_key=api_key,
            model=GEMINI_MODEL,
            small_model=GEMINI_SMALL_MODEL,
        )
        return GeminiClient(config=config)

    elif client_type == "ollama":
        config = LLMConfig(
            api_key="ollama",  # Placeholder, not actually used
            model=OLLAMA_MODEL,
            small_model=OLLAMA_SMALL_MODEL,
            base_url=base_url,
        )
        return OpenAIGenericClient(config=config)

    else:
        raise ValueError(f"Unsupported LLM client type: {client_type}")


def create_embedder_client(
    client_type: str,
    api_key: str | None = None,
    base_url: str | None = None,
    embedding_model: str | None = None,
) -> GeminiEmbedder | OpenAIEmbedder:
    """
    Create an embedder client with hardcoded model names.

    Args:
        client_type: Type of client to create ('gemini' or 'ollama')
        api_key: API key for the client (required for gemini, ignored for ollama)
        base_url: Base URL for the client (optional)
        embedding_model: Override the default embedding model (optional)

    Returns:
        An embedder client instance configured with hardcoded model names
    """
    if client_type == "gemini":
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required for Gemini embedder")
        config = GeminiEmbedderConfig(
            api_key=api_key,
            embedding_model=GEMINI_EMBEDDING_MODEL,
        )
        return GeminiEmbedder(config=config)

    elif client_type == "ollama":
        config = OpenAIEmbedderConfig(
            api_key="ollama",  # Placeholder, not actually used
            embedding_model=OLLAMA_EMBEDDING_MODEL,
            base_url=base_url,
            embedding_dim=768,
        )
        return OpenAIEmbedder(config=config)

    else:
        raise ValueError(f"Unsupported embedder client type: {client_type}")
