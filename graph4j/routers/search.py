"""
Search router with hybrid fact search and supporting endpoints.

This module implements search features including:
- Hybrid search (BM25 + Cosine Similarity)
- RRF (Reciprocal Rank Fusion) reranking
- Center node search for graph-distance-based reranking
"""

from datetime import datetime, timezone

from fastapi import APIRouter, status

from dto import (
    GetMemoryRequest,
    GetMemoryResponse,
    Message,
    SearchQuery,
    SearchResults,
)
from graphiti_client import (
    get_fact_result_from_edge,
    GraphitiDep,
    get_entity_edge as get_entity_edge_helper,
)
from dual_embedding_graphiti import (
    search as search_helper,
)

router = APIRouter()


# Primary search endpoint
@router.post("/search", status_code=status.HTTP_200_OK)
async def search(query: SearchQuery, graphiti: GraphitiDep):
    """
    Primary fact search endpoint using hybrid search.

    This endpoint searches for facts (relationships/edges) in the knowledge graph
    using hybrid search (BM25 + Cosine Similarity) with RRF reranking.
    When a center_node_uuid is provided, results are reranked based on their graph distance from that node for more contextually relevant results.

    Args:
        query: SearchQuery containing:
            - query: The search query string
            - group_ids: Optional list of group IDs to filter results
            - max_facts: Maximum number of facts to return
            - center_node_uuid: Optional UUID of a node to center the search around
            - embedding_mode: Which database to use ("fast" or "quality")

    Returns:
        SearchResults with list of matching facts

    Example:
        POST /search
        {
            "query": "coffee preferences",
            "group_ids": ["user123"],
            "max_facts": 10,
            "center_node_uuid": "some-node-uuid",
            "embedding_mode": "quality"
        }
    """
    relevant_edges = await search_helper(
        fast_client=graphiti.fast_client,
        default_client=graphiti,
        group_ids=query.group_ids or [],
        query=query.query,
        num_results=query.max_facts,
        center_node_uuid=query.center_node_uuid,
        filters=query.filters,
        embedding_mode=query.embedding_mode,
    )
    facts = [get_fact_result_from_edge(edge) for edge in relevant_edges]
    return SearchResults(
        facts=facts,
    )


@router.get("/entity-edge/{uuid}", status_code=status.HTTP_200_OK)
async def get_entity_edge(uuid: str, graphiti: GraphitiDep):
    """Get a specific entity edge by UUID."""
    entity_edge = await get_entity_edge_helper(graphiti, uuid)
    return get_fact_result_from_edge(entity_edge)


@router.get("/episodes/{group_id}", status_code=status.HTTP_200_OK)
async def get_episodes(group_id: str, last_n: int, graphiti: GraphitiDep):
    """Get the most recent episodes for a group."""
    episodes = await graphiti.retrieve_episodes(
        group_ids=[group_id], last_n=last_n, reference_time=datetime.now(timezone.utc)
    )
    return episodes


@router.post("/get-memory", status_code=status.HTTP_200_OK)
async def get_memory(
    request: GetMemoryRequest,
    graphiti: GraphitiDep,
):
    """
    Get memory facts based on a conversation history.

    This endpoint composes a query from multiple messages and searches
    for relevant facts in the knowledge graph.
    """
    combined_query = compose_query_from_messages(request.messages)
    result = await search_helper(
        fast_client=graphiti.fast_client,
        default_client=graphiti,
        group_ids=[request.group_id],
        query=combined_query,
        num_results=request.max_facts,
        center_node_uuid=request.center_node_uuid,
        embedding_mode=request.embedding_mode,
    )
    facts = [get_fact_result_from_edge(edge) for edge in result]
    return GetMemoryResponse(facts=facts)


def compose_query_from_messages(messages: list[Message]):
    """Compose a search query from a list of messages."""
    combined_query = ""
    for message in messages:
        combined_query += (
            f'{message.role_type or ""}({message.role or ""}): {message.content}\n'
        )
    return combined_query
