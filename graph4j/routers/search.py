"""
Advanced search router with hybrid search and reranking capabilities.

This module implements advanced search features including:
- Hybrid search (BM25 + Cosine Similarity)
- RRF (Reciprocal Rank Fusion) reranking
- Entity type filtering
- Center node search for graph-distance-based reranking
"""

from datetime import datetime, timezone

from fastapi import APIRouter, status
from graphiti_core.search.search_config_recipes import NODE_HYBRID_SEARCH_RRF
from graphiti_core.search.search_filters import SearchFilters

from dto import (
    FactResult,
    FactSearchRequest,
    FactSearchResponse,
    GetMemoryRequest,
    GetMemoryResponse,
    Message,
    NodeResult,
    NodeSearchRequest,
    NodeSearchResponse,
    SearchQuery,
    SearchResults,
)
from graphiti_client import (
    get_fact_result_from_edge,
    GraphitiDep,
    get_entity_edge as get_entity_edge_helper,
)

router = APIRouter()


@router.post("/search/nodes", status_code=status.HTTP_200_OK)
async def search_nodes(
    request: NodeSearchRequest, graphiti: GraphitiDep
) -> NodeSearchResponse:
    """
    Advanced node search using hybrid search with RRF reranking.

    This endpoint combines BM25 (keyword-based) and Cosine Similarity (semantic) search,
    then uses Reciprocal Rank Fusion (RRF) to rerank results for optimal relevance.

    Supports dual database architecture:
    - "fast": Searches fast database with fast embeddings
    - "default": Searches quality database with quality embeddings
    - "dual": Searches both databases and merges results

    Args:
        request: NodeSearchRequest containing:
            - query: The search query string
            - group_ids: Optional list of group IDs to filter results
            - max_nodes: Maximum number of nodes to return (default: 10)
            - entity_types: Optional list of entity type names to filter by
            - embedding_mode: Which database to search ("fast", "default", or "dual")
        graphiti: Injected Graphiti client dependency

    Returns:
        NodeSearchResponse with list of matching nodes

    Example:
        POST /search/nodes
        {
            "query": "user preferences for coffee",
            "group_ids": ["user123"],
            "max_nodes": 5,
            "entity_types": ["Preference", "Requirement"],
            "embedding_mode": "dual"
        }
    """
    from dual_embedding_graphiti import search_nodes_dual

    # Create search filters for entity types
    search_filters = SearchFilters(
        node_labels=request.entity_types,
    )

    # Use dual database search
    results = await search_nodes_dual(
        fast_client=graphiti.fast_client,
        quality_client=graphiti.quality_client,
        query=request.query,
        config=NODE_HYBRID_SEARCH_RRF,
        group_ids=request.group_ids or [],
        search_filter=search_filters,
        embedding_mode=request.embedding_mode,
    )

    # Extract nodes from results
    nodes = results.nodes[: request.max_nodes] if results.nodes else []

    if not nodes:
        return NodeSearchResponse(nodes=[])

    # Format the results
    node_results = []
    for node in nodes:
        # Get attributes and ensure no embeddings are included
        attrs = node.attributes if hasattr(node, "attributes") else {}
        # Remove any embedding keys that might be in attributes
        attrs = {k: v for k, v in attrs.items() if "embedding" not in k.lower()}

        node_results.append(
            NodeResult(
                uuid=node.uuid,
                name=node.name,
                labels=node.labels if node.labels else [],
                created_at=node.created_at.isoformat() if node.created_at else None,
                summary=node.summary,
                group_id=node.group_id,
                attributes=attrs,
            )
        )

    return NodeSearchResponse(nodes=node_results)


@router.post("/search/facts", status_code=status.HTTP_200_OK)
async def search_facts(
    request: FactSearchRequest, graphiti: GraphitiDep
) -> FactSearchResponse:
    """
    Advanced fact/edge search with optional center node reranking.

    This endpoint searches for facts (relationships/edges) in the knowledge graph.
    When a center_node_uuid is provided, results are reranked based on their
    graph distance from that node, providing more contextually relevant results.

    Supports dual database architecture:
    - "fast": Searches fast database with fast embeddings
    - "default": Searches quality database with quality embeddings
    - "dual": Searches both databases and merges results

    Args:
        request: FactSearchRequest containing:
            - query: The search query string
            - group_ids: Optional list of group IDs to filter results
            - max_facts: Maximum number of facts to return (default: 10)
            - center_node_uuid: Optional UUID of a node to center the search around
            - embedding_mode: Which database to search ("fast", "default", or "dual")
        graphiti: Injected Graphiti client dependency

    Returns:
        FactSearchResponse with list of matching facts

    Example:
        POST /search/facts
        {
            "query": "coffee preferences",
            "group_ids": ["user123"],
            "max_facts": 10,
            "center_node_uuid": "some-node-uuid",
            "embedding_mode": "dual"
        }
    """
    from dual_embedding_graphiti import search_dual

    if request.max_facts <= 0:
        return FactSearchResponse(facts=[])

    # Use dual database search
    relevant_edges = await search_dual(
        fast_client=graphiti.fast_client,
        quality_client=graphiti.quality_client,
        query=request.query,
        group_ids=request.group_ids or [],
        num_results=request.max_facts,
        center_node_uuid=request.center_node_uuid,
        embedding_mode=request.embedding_mode,
    )

    if not relevant_edges:
        return FactSearchResponse(facts=[])

    facts = [get_fact_result_from_edge(edge) for edge in relevant_edges]
    return FactSearchResponse(facts=facts)


# Legacy endpoints for backward compatibility
@router.post("/search", status_code=status.HTTP_200_OK)
async def search(query: SearchQuery, graphiti: GraphitiDep):
    """
    Legacy search endpoint for backward compatibility.

    For new implementations, use /search/facts or /search/nodes instead.
    """
    relevant_edges = await graphiti.search(
        group_ids=query.group_ids,
        query=query.query,
        num_results=query.max_facts,
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
    result = await graphiti.search(
        group_ids=[request.group_id],
        query=combined_query,
        num_results=request.max_facts,
        center_node_uuid=request.center_node_uuid,
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
