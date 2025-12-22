import logging
from typing import Annotated

from fastapi import Depends, HTTPException
from graphiti_core import Graphiti
from graphiti_core.edges import EntityEdge
from graphiti_core.errors import (
    EdgeNotFoundError,
    GroupsEdgesNotFoundError,
    NodeNotFoundError,
)
from graphiti_core.llm_client import LLMClient, LLMConfig, OpenAIClient
from graphiti_core.embedder import EmbedderClient, OpenAIEmbedder, OpenAIEmbedderConfig
from graphiti_core.nodes import EntityNode, EpisodicNode

from config import SettingsDep
from dto import FactResult

logger = logging.getLogger(__name__)


# Helper functions for operations used by routers
async def get_entity_edge(graphiti: Graphiti, uuid: str) -> EntityEdge:
    """Get an entity edge by UUID."""
    try:
        edge = await EntityEdge.get_by_uuid(graphiti.driver, uuid)
        return edge
    except EdgeNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message) from e


async def delete_entity_edge(graphiti: Graphiti, uuid: str):
    """Delete an entity edge by UUID (supports dual databases)."""

    # Helper to delete from a single driver
    async def _delete(client):
        try:
            edge = await EntityEdge.get_by_uuid(client.driver, uuid)
            await edge.delete(client.driver)
        except EdgeNotFoundError:
            # Silently ignore if not found in one of the databases
            pass

    # Delete from default database
    await _delete(graphiti)

    # Delete from fast database if it exists
    if hasattr(graphiti, "fast_client") and graphiti.fast_client:
        await _delete(graphiti.fast_client)


async def delete_episodic_node(graphiti: Graphiti, uuid: str):
    """Delete an episodic node by UUID (supports dual databases)."""

    # Helper to delete from a single driver
    async def _delete(client):
        try:
            episode = await EpisodicNode.get_by_uuid(client.driver, uuid)
            await episode.delete(client.driver)
        except NodeNotFoundError:
            pass

    # Delete from default database
    await _delete(graphiti)

    # Delete from fast database if it exists
    if hasattr(graphiti, "fast_client") and graphiti.fast_client:
        await _delete(graphiti.fast_client)


async def delete_group(graphiti: Graphiti, group_id: str):
    """Delete all nodes and edges in a group (supports dual databases)."""

    # Helper to delete from a single driver
    async def _delete(client):
        try:
            edges = await EntityEdge.get_by_group_ids(client.driver, [group_id])
        except GroupsEdgesNotFoundError:
            edges = []

        nodes = await EntityNode.get_by_group_ids(client.driver, [group_id])
        episodes = await EpisodicNode.get_by_group_ids(client.driver, [group_id])

        for edge in edges:
            await edge.delete(client.driver)
        for node in nodes:
            await node.delete(client.driver)
        for episode in episodes:
            await episode.delete(client.driver)

    # Delete from default database
    await _delete(graphiti)

    # Delete from fast database if it exists
    if hasattr(graphiti, "fast_client") and graphiti.fast_client:
        await _delete(graphiti.fast_client)


# Global long-lived Graphiti clients
_default_graphiti: Graphiti | None = None
_fast_graphiti: Graphiti | None = None


async def get_graphiti(settings: SettingsDep):
    """Dependency to get long-lived Graphiti client instances for dual database architecture.

    Returns the main graphiti instance with fast_client attached as an attribute
    for dual database operations.

    These clients are initialized once on application startup and reused across all requests.
    They are closed only when the application shuts down.
    """
    global _default_graphiti, _fast_graphiti

    if _default_graphiti is None or _fast_graphiti is None:
        raise RuntimeError(
            "Graphiti clients not initialized. Call initialize_graphiti() during startup."
        )

    # Return the main graphiti instance (already has fast_client attached)
    yield _default_graphiti


def get_clients() -> tuple[Graphiti, Graphiti]:
    """Helper for background tasks to get initialized clients."""
    if _default_graphiti is None or _fast_graphiti is None:
        raise RuntimeError("Graphiti clients not initialized")
    return _default_graphiti, _fast_graphiti


async def initialize_graphiti(settings: SettingsDep):
    """Initialize long-lived Graphiti clients for both databases.

    This should be called once during application startup.
    """
    global _default_graphiti, _fast_graphiti

    logger.info(f"Initializing LLM client with model: {settings.model_name}")
    llm_client = OpenAIClient(
        config=LLMConfig(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.model_name,
            # Set small_model to prevent graphiti_core from using hardcoded 'gpt-5-nano' default
            small_model=settings.model_name,
        )
    )
    logger.info(
        f"LLM client initialized. Model: {llm_client.model}, Small model: {llm_client.small_model}"
    )

    # Create both embedders
    fast_embedder = OpenAIEmbedder(
        config=OpenAIEmbedderConfig(
            embedding_model=settings.fast_embedding_model,
            api_key=settings.openai_api_key,
            base_url=settings.fast_base_url,
        )
    )

    embedder = OpenAIEmbedder(
        config=OpenAIEmbedderConfig(
            embedding_model=settings.embedding_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
    )

    # Create fast database client
    _fast_graphiti = Graphiti(
        uri=settings.neo4j_fast_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
        llm_client=llm_client,
        embedder=fast_embedder,
    )

    # Create default database client
    _default_graphiti = Graphiti(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
        llm_client=llm_client,
        embedder=embedder,
    )

    # Store fast_client reference for dual database operations
    _default_graphiti.fast_client = _fast_graphiti
    _default_graphiti.fast_embedder = fast_embedder

    is_dual_db = settings.neo4j_fast_uri != settings.neo4j_uri

    logger.info(
        f"Initialized Graphiti clients ({'DUAL DATABASE' if is_dual_db else 'SINGLE DATABASE'} mode):\n"
        f"  Fast: {settings.fast_embedding_model} @ {settings.fast_base_url}\n"
        f"    Database: {settings.neo4j_fast_uri}\n"
        f"  Default: {settings.embedding_model} @ {settings.openai_base_url}\n"
        f"    Database: {settings.neo4j_uri}"
    )

    # Build indices for default database
    await _default_graphiti.build_indices_and_constraints()
    logger.info(
        f"Initialized indices and constraints for default database: {settings.neo4j_uri}"
    )

    # Build indices for fast database (if different from default)
    if is_dual_db:
        await _fast_graphiti.build_indices_and_constraints()
        logger.info(
            f"Initialized indices and constraints for fast database: {settings.neo4j_fast_uri}"
        )


async def close_graphiti():
    """Close long-lived Graphiti clients.

    This should be called once during application shutdown.
    """
    global _default_graphiti, _fast_graphiti

    if _default_graphiti is not None:
        await _default_graphiti.close()
        logger.info("Closed default Graphiti client")

    if _fast_graphiti is not None and _fast_graphiti is not _default_graphiti:
        await _fast_graphiti.close()
        logger.info("Closed fast Graphiti client")

    _default_graphiti = None
    _fast_graphiti = None


def get_fact_result_from_edge(edge: EntityEdge):
    """Convert EntityEdge to FactResult DTO."""
    return FactResult(
        uuid=edge.uuid,
        name=edge.name,
        fact=edge.fact,
        valid_at=edge.valid_at,
        invalid_at=edge.invalid_at,
        created_at=edge.created_at,
        expired_at=edge.expired_at,
    )


GraphitiDep = Annotated[Graphiti, Depends(get_graphiti)]
