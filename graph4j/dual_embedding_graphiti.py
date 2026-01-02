import asyncio
import logging
from datetime import datetime

from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType  # EntityNode, EpisodicNode
from graphiti_core.search.search_filters import SearchFilters


from graphiti_core.search.search_config import SearchConfig
from graphiti_core.search.search_config_recipes import (
    EDGE_HYBRID_SEARCH_RRF,
    EDGE_HYBRID_SEARCH_NODE_DISTANCE,
)


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
) -> None:
    """
    Add an episode to both fast and default databases with single LLM extraction.

    This function performs LLM extraction ONCE using the fast graphiti client, then saves the same extracted nodes/edges to both databases.
    To support realtime operations, it awaits the fast save but fires and forgets the default save.

    Args:
        fast_graphiti: Graphiti client connected to fast database
        default_graphiti: Graphiti client connected to default database
        uuid: Unique identifier for the episode
        group_id: Group identifier for organizing episodes
        name: Name/title of the episode
        episode_body: The content to extract knowledge from
        reference_time: Timestamp for the episode
        source: Type of episode content (message, text, or json)
        source_description: Optional description of the source
    """
    logger.info(
        f"Adding episode to dual databases:\n"
        f"  Episode: {name}\n"
        f"  Group: {group_id}\n"
    )

    # Step 1: Sequential save to fast database (high priority)
    # This includes the LLM extraction
    fast_result = await fast_graphiti.add_episode(
        uuid=uuid,
        group_id=group_id,
        name=name,
        episode_body=episode_body,
        reference_time=reference_time,
        source=source,
        source_description=source_description,
    )

    logger.info(f"Fast save complete for '{name}'. Starting background quality save.")

    # Step 2: Fire and forget save to default database (lower priority)
    # We use create_task to background the slower quality embedding generation/save
    # This allows realtime operations to proceed as soon as the fast save is done
    asyncio.create_task(
        default_graphiti.save_episode_results(
            episode=fast_result.episode,
            nodes=fast_result.nodes,
            edges=fast_result.edges,
            episodic_edges=fast_result.episodic_edges,
            embedder=default_graphiti.embedder,
            clear_embeddings=True,
        )
    )


async def search(
    fast_client: Graphiti,
    default_client: Graphiti,
    query: str,
    group_ids: list[str],
    num_results: int = 3,
    center_node_uuid: str | None = None,
    filters: SearchFilters | None = None,
    embedding_mode: str = "quality",
    reranker_min_score: float | None = None,
    min_sim_score: float | None = None,
):
    """
    Search across databases based on embedding mode.

    Args:
        fast_client: Graphiti client connected to fast database
        default_client: Graphiti client connected to default database
        query: Search query string
        group_ids: List of group IDs to filter results
        num_results: Maximum number of results to return
        center_node_uuid: Optional center node for graph-distance reranking
        filters: Optional structured filters (labels, properties, etc.)
        embedding_mode: Which database to search ("fast" or "quality")
        reranker_min_score: Optional minimum score for reranking
        min_sim_score: Optional minimum similarity score for vector search

    Returns:
        Search results from the appropriate database(s)
    """
    # Default to empty filters if None
    search_filters = filters or SearchFilters()

    # Configure search based on whether a center node is provided
    # Use model_copy to avoid modifying the recipe constants
    search_config: SearchConfig = (
        EDGE_HYBRID_SEARCH_RRF
        if center_node_uuid is None
        else EDGE_HYBRID_SEARCH_NODE_DISTANCE
    ).model_copy(deep=True)

    search_config.limit = num_results
    if reranker_min_score is not None:
        search_config.reranker_min_score = reranker_min_score

    if min_sim_score is not None and search_config.edge_config is not None:
        search_config.edge_config.sim_min_score = min_sim_score

    if embedding_mode == "fast":
        # Search only fast database
        logger.debug(f"Searching fast database for: {query}")
        results = await fast_client.search_(
            group_ids=group_ids,
            query=query,
            config=search_config,
            center_node_uuid=center_node_uuid,
            search_filter=search_filters,
        )
        return results.edges

    elif embedding_mode == "quality":
        # Search only quality database
        logger.debug(f"Searching quality database for: {query}")
        results = await default_client.search_(
            group_ids=group_ids,
            query=query,
            config=search_config,
            center_node_uuid=center_node_uuid,
            search_filter=search_filters,
        )
        return results.edges

    else:
        raise ValueError(f"Invalid embedding_mode: {embedding_mode}")


# def is_dual_database_mode(fast_client: Graphiti, default_client: Graphiti) -> bool:
#     """
#     Check if the system is running in dual database mode.

#     Args:
#         fast_client: Graphiti client connected to fast database
#         default_client: Graphiti client connected to default database

#     Returns:
#         True if using separate databases, False if using same database
#     """
#     return fast_client.driver.uri != default_client.driver.uri
