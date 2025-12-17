import asyncio
import logging
from typing import Any

from graphiti_core import Graphiti
from graphiti_core.nodes import EntityNode, EpisodicNode, EpisodeType
from datetime import datetime

logger = logging.getLogger(__name__)


async def add_episode_dual(
    fast_graphiti: Graphiti,
    default_graphiti: Graphiti,
    uuid: str,
    group_id: str,
    name: str,
    episode_body: str,
    reference_time: datetime,
    source: EpisodeType = EpisodeType.message,
    source_description: str | None = None,
) -> tuple[Any, Any]:
    """
    Add an episode to both fast and default databases with single LLM extraction.

    This function performs LLM extraction ONCE using the fast graphiti client, then saves the same extracted nodes/edges to both databases with their respective embeddings.
    This is significantly more efficient than calling add_episode twice.

    Args:
        fast_graphiti: Graphiti client connected to fast database
        default graphiti: Graphiti client connected to default database
        uuid: Unique identifier for the episode
        group_id: Group identifier for organizing episodes
        name: Name/title of the episode
        episode_body: The content to extract knowledge from
        reference_time: Timestamp for the episode
        source: Type of episode content (message, text, or json)
        source_description: Optional description of the source

    Returns:
        Tuple of (fast_result, default_result) from both database saves
    """
    logger.info(
        f"Adding episode to dual databases (single extraction):\n"
        f"  Episode: {name}\n"
        f"  Group: {group_id}\n"
        f"  Fast DB: {fast_graphiti.driver.uri}\n"
        f"  Default DB: {default_graphiti.driver.uri}"
    )

    # Step 1: Extract using fast client (LLM extraction + fast embeddings)
    # This is the ONLY LLM call - we reuse the extraction for default database
    fast_result = await fast_graphiti.add_episode(
        uuid=uuid,
        group_id=group_id,
        name=name,
        episode_body=episode_body,
        reference_time=reference_time,
        source=source,
        source_description=source_description,
    )

    logger.info(
        f"Fast extraction complete:\n"
        f"  Nodes: {len(fast_result.nodes)}\n"
        f"  Edges: {len(fast_result.edges)}\n"
        f"  Episode saved to fast database"
    )

    # Step 2: Save the same extracted results to default database with default embeddings
    # save_episode_results will deep copy and clear embeddings automatically
    default_result = await default_graphiti.save_episode_results(
        episode=fast_result.episode,
        nodes=fast_result.nodes,
        edges=fast_result.edges,
        episodic_edges=fast_result.episodic_edges,
        embedder=default_graphiti.embedder,  # Use default embedder
        clear_embeddings=True,  # Clear embeddings before regenerating
    )

    logger.info(
        f"Default save complete:\n"
        f"  Nodes: {len(default_result.nodes)}\n"
        f"  Edges: {len(default_result.edges)}\n"
        f"  Episode saved to default database with default embeddings"
    )

    return fast_result, default_result


async def search_dual(
    fast_client: Graphiti,
    default_client: Graphiti,
    query: str,
    group_ids: list[str],
    num_results: int = 10,
    center_node_uuid: str | None = None,
    embedding_mode: str = "default",
):
    """
    Search across dual databases based on embedding mode.

    Args:
        fast_client: Graphiti client connected to fast database
        default_client: Graphiti client connected to default database
        query: Search query string
        group_ids: List of group IDs to filter results
        num_results: Maximum number of results to return
        center_node_uuid: Optional center node for graph-distance reranking
        embedding_mode: Which database to search ("fast", "default", or "dual")

    Returns:
        Search results from the appropriate database(s)
    """
    if embedding_mode == "fast":
        # Search only fast database
        logger.debug(f"Searching fast database for: {query}")
        return await fast_client.search(
            group_ids=group_ids,
            query=query,
            num_results=num_results,
            center_node_uuid=center_node_uuid,
        )

    elif embedding_mode == "default":
        # Search only default database
        logger.debug(f"Searching default database for: {query}")
        return await default_client.search(
            group_ids=group_ids,
            query=query,
            num_results=num_results,
            center_node_uuid=center_node_uuid,
        )

    elif embedding_mode == "dual":
        # Search both databases and merge results
        logger.debug(f"Searching both databases for: {query}")

        # Search both databases in parallel
        fast_results, default_results = await asyncio.gather(
            fast_client.search(
                group_ids=group_ids,
                query=query,
                num_results=num_results,
                center_node_uuid=center_node_uuid,
            ),
            default_client.search(
                group_ids=group_ids,
                query=query,
                num_results=num_results,
                center_node_uuid=center_node_uuid,
            ),
        )

        # Merge results (simple concatenation, could be improved with deduplication)
        # Default results are prioritized by being placed first
        merged = default_results + fast_results
        return merged[:num_results]

    else:
        raise ValueError(f"Invalid embedding_mode: {embedding_mode}")


async def search_nodes_dual(
    fast_client: Graphiti,
    default_client: Graphiti,
    query: str,
    config: Any,
    group_ids: list[str],
    search_filter: Any = None,
    embedding_mode: str = "default",
):
    """
    Advanced node search across dual databases with custom config.

    Args:
        fast_client: Graphiti client connected to fast database
        default_client: Graphiti client connected to default database
        query: Search query string
        config: Search configuration (e.g., NODE_HYBRID_SEARCH_RRF)
        group_ids: List of group IDs to filter results
        search_filter: Optional search filters
        embedding_mode: Which database to search ("fast", "default", or "dual")

    Returns:
        Search results from the appropriate database(s)
    """
    if embedding_mode == "fast":
        # Search only fast database
        logger.debug(f"Searching fast database (advanced) for: {query}")
        return await fast_client.search_(
            query=query,
            config=config,
            group_ids=group_ids,
            search_filter=search_filter,
        )

    elif embedding_mode == "default":
        # Search only default database
        logger.debug(f"Searching default database (advanced) for: {query}")
        return await default_client.search_(
            query=query,
            config=config,
            group_ids=group_ids,
            search_filter=search_filter,
        )

    elif embedding_mode == "dual":
        # Search both databases and merge results
        logger.debug(f"Searching both databases (advanced) for: {query}")

        # Search both databases in parallel
        fast_results, default_results = await asyncio.gather(
            fast_client.search_(
                query=query,
                config=config,
                group_ids=group_ids,
                search_filter=search_filter,
            ),
            default_client.search_(
                query=query,
                config=config,
                group_ids=group_ids,
                search_filter=search_filter,
            ),
        )

        # Merge node results (default prioritized)
        merged_nodes = default_results.nodes + fast_results.nodes
        default_results.nodes = merged_nodes
        return default_results

    else:
        raise ValueError(f"Invalid embedding_mode: {embedding_mode}")


def is_dual_database_mode(fast_client: Graphiti, default_client: Graphiti) -> bool:
    """
    Check if the system is running in dual database mode.

    Args:
        fast_client: Graphiti client connected to fast database
        default_client: Graphiti client connected to default database

    Returns:
        True if using separate databases, False if using same database
    """
    return fast_client.driver.uri != default_client.driver.uri
