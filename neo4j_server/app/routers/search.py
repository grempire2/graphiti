from fastapi import APIRouter, status

from graphiti_core.search.search_config_recipes import (
    COMBINED_HYBRID_SEARCH_MMR,
    EDGE_HYBRID_SEARCH_NODE_DISTANCE,
)
from graphiti_core.search.search_utils import DEFAULT_MIN_SCORE

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
        settings,
        request.llm_client or settings.llm_client,
        request.embedder_client or settings.embedder_client,
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
    Perform a center node search using graphiti.search_() with center_node_uuid.

    This endpoint reranks search results based on their graph distance
    to a specific center node, providing more contextually relevant results.
    """
    graphiti = create_graphiti_client(
        settings,
        request.llm_client or settings.llm_client,
        request.embedder_client or settings.embedder_client,
    )
    try:
        # Use node distance config for center node search (same as graphiti.search() uses internally)
        search_config = EDGE_HYBRID_SEARCH_NODE_DISTANCE.model_copy(deep=True)
        search_config.limit = request.num_results

        # sim_min_score uses default from graphiti_core (DEFAULT_MIN_SCORE)
        # Since BM25 and cosine similarity run in parallel and results are reranked,
        # we rely on reranker_min_score for final filtering

        # Apply reranker_min_score to filter results after reranking
        # This is the primary filter - reranking gives better relevance scores
        # Default to DEFAULT_MIN_SCORE
        warnings = []
        search_config.reranker_min_score = DEFAULT_MIN_SCORE

        results = await graphiti.search_(
            query=request.query,
            config=search_config,
            group_ids=request.group_ids,
            center_node_uuid=request.center_node_uuid,
        )
        facts = [fact_result_from_edge(edge) for edge in results.edges]
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
        settings,
        request.llm_client or settings.llm_client,
        request.embedder_client or settings.embedder_client,
    )
    try:
        # Use MMR reranker for better semantic relevance
        # MMR uses query similarity directly, providing better quality than RRF
        search_config = COMBINED_HYBRID_SEARCH_MMR.model_copy(deep=True)

        # sim_min_score uses default from graphiti_core (DEFAULT_MIN_SCORE)
        # Since BM25 and cosine similarity run in parallel and results are reranked,
        # we rely on reranker_min_score for final filtering rather than early filtering

        # Apply reranker_min_score to filter results after reranking
        # This is the primary filter - reranking gives better relevance scores than early filtering
        warnings = []
        if request.reranker_min_score is not None:
            search_config.reranker_min_score = request.reranker_min_score
        else:
            search_config.reranker_min_score = DEFAULT_MIN_SCORE

        results = await graphiti.search_(
            query=request.query,
            config=search_config,
            group_ids=request.group_ids,
            center_node_uuid=request.center_node_uuid,
        )

        # Apply return_limit if specified, otherwise use all results (limited by search_config.limit)
        final_limit = request.return_limit

        # Convert edges to facts
        facts = [
            fact_result_from_edge(edge)
            for edge in (results.edges[:final_limit] if final_limit else results.edges)
        ]

        return AdvancedSearchResponse(
            facts=facts,
            edges=facts,  # Keep edges for backward compatibility
            nodes=[
                node_to_dict(node)
                for node in (
                    results.nodes[:final_limit] if final_limit else results.nodes
                )
            ],
            episodes=[
                episode_to_dict(episode)
                for episode in (
                    results.episodes[:final_limit] if final_limit else results.episodes
                )
            ],
            communities=[
                community_to_dict(community)
                for community in (
                    results.communities[:final_limit]
                    if final_limit
                    else results.communities
                )
            ],
            warnings=warnings,
        )
    finally:
        await graphiti.close()
