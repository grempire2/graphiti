from fastapi import APIRouter, status

from graphiti_core.search.search_config_recipes import (
    COMBINED_HYBRID_SEARCH_MMR,
)

from app.config import SettingsDep
from app.dto import (
    AdvancedSearchRequest,
    AdvancedSearchResponse,
    BasicSearchRequest,
    BasicSearchResponse,
    CenterNodeSearchRequest,
    CenterNodeSearchResponse,
    community_to_dict,
    episode_to_dict,
    fact_result_from_edge,
    node_to_dict,
)
from app.graphiti_client import create_graphiti_client

router = APIRouter()


@router.post("/search/basic", status_code=status.HTTP_200_OK)
async def basic_search(request: BasicSearchRequest, settings: SettingsDep):
    """
    Perform a basic search using graphiti.search().

    This endpoint performs a hybrid search combining semantic similarity
    and BM25 text retrieval, returning edges (facts) from the graph.
    """
    graphiti = create_graphiti_client(
        settings, request.llm_client, request.embedder_client
    )
    try:
        edges = await graphiti.search(
            query=request.query,
            group_ids=request.group_ids,
            num_results=request.num_results,
        )
        facts = [fact_result_from_edge(edge) for edge in edges]
        return BasicSearchResponse(facts=facts)
    finally:
        await graphiti.close()


@router.post("/search/center", status_code=status.HTTP_200_OK)
async def center_node_search(request: CenterNodeSearchRequest, settings: SettingsDep):
    """
    Perform a center node search using graphiti.search() with center_node_uuid.

    This endpoint reranks search results based on their graph distance
    to a specific center node, providing more contextually relevant results.
    """
    graphiti = create_graphiti_client(
        settings, request.llm_client, request.embedder_client
    )
    try:
        edges = await graphiti.search(
            query=request.query,
            center_node_uuid=request.center_node_uuid,
            group_ids=request.group_ids,
            num_results=request.num_results,
        )
        facts = [fact_result_from_edge(edge) for edge in edges]
        return CenterNodeSearchResponse(facts=facts)
    finally:
        await graphiti.close()


@router.post("/search/advanced", status_code=status.HTTP_200_OK)
async def advanced_search(request: AdvancedSearchRequest, settings: SettingsDep):
    """
    Perform an advanced search using graphiti.search_().

    This endpoint uses the advanced search method that returns Graph objects
    (nodes, edges, episodes, communities) rather than just facts. It supports
    more advanced features such as filters and different search methodologies.
    """
    graphiti = create_graphiti_client(
        settings, request.llm_client, request.embedder_client
    )
    try:
        # Use MMR reranker for better semantic relevance
        # MMR uses query similarity directly, providing better quality than RRF
        search_config = COMBINED_HYBRID_SEARCH_MMR.model_copy(deep=True)
        search_config.limit = request.limit

        results = await graphiti.search_(
            query=request.query,
            config=search_config,
            group_ids=request.group_ids,
            center_node_uuid=request.center_node_uuid,
        )

        return AdvancedSearchResponse(
            edges=[fact_result_from_edge(edge) for edge in results.edges],
            nodes=[node_to_dict(node) for node in results.nodes],
            episodes=[episode_to_dict(episode) for episode in results.episodes],
            communities=[
                community_to_dict(community) for community in results.communities
            ],
        )
    finally:
        await graphiti.close()
