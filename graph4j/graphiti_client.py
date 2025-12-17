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
from graphiti_core.llm_client import LLMClient, OpenAIClient
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
    """Delete an entity edge by UUID."""
    try:
        edge = await EntityEdge.get_by_uuid(graphiti.driver, uuid)
        await edge.delete(graphiti.driver)
    except EdgeNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message) from e


async def delete_episodic_node(graphiti: Graphiti, uuid: str):
    """Delete an episodic node by UUID."""
    try:
        episode = await EpisodicNode.get_by_uuid(graphiti.driver, uuid)
        await episode.delete(graphiti.driver)
    except NodeNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message) from e


async def delete_group(graphiti: Graphiti, group_id: str):
    """Delete all nodes and edges in a group."""
    try:
        edges = await EntityEdge.get_by_group_ids(graphiti.driver, [group_id])
    except GroupsEdgesNotFoundError:
        logger.warning(f"No edges found for group {group_id}")
        edges = []

    nodes = await EntityNode.get_by_group_ids(graphiti.driver, [group_id])
    episodes = await EpisodicNode.get_by_group_ids(graphiti.driver, [group_id])

    for edge in edges:
        await edge.delete(graphiti.driver)

    for node in nodes:
        await node.delete(graphiti.driver)

    for episode in episodes:
        await episode.delete(graphiti.driver)


async def get_graphiti(settings: SettingsDep):
    """Dependency to get Graphiti client instances for dual database architecture.

    Creates two separate Graphiti clients:
    - fast_client: Connected to fast database with fast embedder
    - quality_client: Connected to quality database with quality embedder

    Both clients share the same LLM client for extraction.

    The main client (quality_client) is returned for backward compatibility,
    but both clients are stored as attributes for dual database operations.

    Embedding mode is determined per-request via the API, not via configuration.
    """
    llm_client = OpenAIClient(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        model=settings.model_name,
    )

    # ALWAYS create both embedders during startup
    # Both are ready for immediate use based on per-request mode selection
    fast_embedder = OpenAIEmbedder(
        config=OpenAIEmbedderConfig(
            embedding_model=settings.fast_embedding_model,
            api_key=settings.openai_api_key,
            base_url=settings.fast_base_url,
        )
    )

    quality_embedder = OpenAIEmbedder(
        config=OpenAIEmbedderConfig(
            embedding_model=settings.embedding_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
    )

    # Create fast database client
    fast_client = Graphiti(
        uri=settings.neo4j_fast_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
        llm_client=llm_client,
        embedder=fast_embedder,
    )

    # Create quality database client
    quality_client = Graphiti(
        uri=settings.neo4j_quality_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
        llm_client=llm_client,
        embedder=quality_embedder,
    )

    # Store references for dual database operations
    # Main client is quality_client for backward compatibility
    quality_client.fast_client = fast_client
    quality_client.quality_client = quality_client
    quality_client.fast_embedder = fast_embedder
    quality_client.default_embedder = quality_embedder

    is_dual_db = settings.neo4j_fast_uri != settings.neo4j_quality_uri

    logger.info(
        f"Initialized Graphiti clients ({'DUAL DATABASE' if is_dual_db else 'SINGLE DATABASE'} mode):\n"
        f"  Fast: {settings.fast_embedding_model} @ {settings.fast_base_url}\n"
        f"    Database: {settings.neo4j_fast_uri}\n"
        f"  Quality: {settings.embedding_model} @ {settings.openai_base_url}\n"
        f"    Database: {settings.neo4j_quality_uri}"
    )

    try:
        yield quality_client
    finally:
        await quality_client.close()
        # Only close fast_client if it's a different database
        if is_dual_db:
            await fast_client.close()


async def initialize_graphiti(settings: SettingsDep):
    """Initialize Graphiti indices and constraints."""
    client = Graphiti(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
    )
    await client.build_indices_and_constraints()


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
