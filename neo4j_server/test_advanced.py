"""
Test script for search functionality (basic, center node, and advanced).

This script tests all search endpoints:
- Basic search: Returns facts (edges) using hybrid search
- Center node search: Reranks results based on graph distance to a center node
- Advanced search: Returns nodes, edges, episodes, and communities

It assumes data already exists in the Neo4j database.

NOTE: The advanced search endpoint uses COMBINED_HYBRID_SEARCH_MMR
which uses MMR (Maximal Marginal Relevance) reranking for better semantic
relevance compared to RRF (Reciprocal Rank Fusion).

Search Quality Comparison:
- MMR: Better for semantic relevance (uses query similarity directly)
- RRF: Good for combining multiple search method results (consensus-based)
- Center Node: Adds graph context, improving relevance when you have a
  specific entity/context to focus on

Best Practice: Use center_node_uuid when you have a specific entity context
to get more relevant results through graph distance reranking.
"""

import asyncio
import logging
import os
import time
from logging import INFO

import httpx
from dotenv import load_dotenv

#################################################
# CONFIGURATION
#################################################
# Set up logging and environment variables for
# connecting to the Neo4j Graphiti server
#################################################

# Configure logging
logging.basicConfig(
    level=INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

load_dotenv()

# Server configuration
SERVER_URL = os.environ.get("SERVER_URL", "http://localhost:18888")
API_BASE = f"{SERVER_URL}/api/v1"

# Default client configuration (can be overridden)
DEFAULT_LLM_CLIENT = os.environ.get("LLM_CLIENT", "groq")
DEFAULT_EMBEDDER_CLIENT = os.environ.get("EMBEDDER_CLIENT", "gemini")


async def basic_search(
    client: httpx.AsyncClient,
    query: str,
    llm_client: str = DEFAULT_LLM_CLIENT,
    embedder_client: str = DEFAULT_EMBEDDER_CLIENT,
    group_ids: list[str] | None = None,
    num_results: int = 10,
) -> dict:
    """
    Perform a basic search.
    
    The simplest way to retrieve relationships (edges) from Graphiti.
    Performs a hybrid search combining semantic similarity and BM25 text retrieval.
    Returns facts (edges) that match the query.
    """
    payload = {
        "query": query,
        "llm_client": llm_client,
        "embedder_client": embedder_client,
        "num_results": num_results,
    }
    if group_ids:
        payload["group_ids"] = group_ids

    response = await client.post(f"{API_BASE}/search/basic", json=payload)
    response.raise_for_status()
    return response.json()


async def center_node_search(
    client: httpx.AsyncClient,
    query: str,
    center_node_uuid: str,
    llm_client: str = DEFAULT_LLM_CLIENT,
    embedder_client: str = DEFAULT_EMBEDDER_CLIENT,
    group_ids: list[str] | None = None,
    num_results: int = 10,
) -> dict:
    """
    Perform a center node search.
    
    For more contextually relevant results, reranks search results based
    on their graph distance to a specific node. This provides better
    contextual relevance when you have a specific entity/context to focus on.
    """
    payload = {
        "query": query,
        "center_node_uuid": center_node_uuid,
        "llm_client": llm_client,
        "embedder_client": embedder_client,
        "num_results": num_results,
    }
    if group_ids:
        payload["group_ids"] = group_ids

    response = await client.post(f"{API_BASE}/search/center", json=payload)
    response.raise_for_status()
    return response.json()


async def advanced_search(
    client: httpx.AsyncClient,
    query: str,
    llm_client: str = DEFAULT_LLM_CLIENT,
    embedder_client: str = DEFAULT_EMBEDDER_CLIENT,
    group_ids: list[str] | None = None,
    center_node_uuid: str | None = None,
    limit: int = 10,
) -> dict:
    """
    Perform an advanced search.
    
    This endpoint uses COMBINED_HYBRID_SEARCH_MMR which:
    - Combines BM25 (fulltext) + cosine similarity (vector) search
    - Uses MMR reranking for better semantic relevance (query similarity)
    - Returns nodes, edges, episodes, and communities
    
    For even better quality, use center_node_uuid to add graph context reranking.
    The center node reranks results based on graph distance, providing more
    contextually relevant results when you have a specific entity focus.
    """
    payload = {
        "query": query,
        "llm_client": llm_client,
        "embedder_client": embedder_client,
        "limit": limit,
    }
    if group_ids:
        payload["group_ids"] = group_ids
    if center_node_uuid:
        payload["center_node_uuid"] = center_node_uuid

    response = await client.post(f"{API_BASE}/search/advanced", json=payload)
    response.raise_for_status()
    return response.json()


def print_search_results(results: dict, query: str):
    """Print formatted search results."""
    edges = results.get("edges", [])
    nodes = results.get("nodes", [])
    episodes = results.get("episodes", [])
    communities = results.get("communities", [])

    print(f"\nQuery: '{query}'")
    print(f"  Edges (facts): {len(edges)}")
    print(f"  Nodes: {len(nodes)}")
    print(f"  Episodes: {len(episodes)}")
    print(f"  Communities: {len(communities)}")

    if edges:
        print("\n  Top Edges:")
        for i, edge in enumerate(edges[:5], 1):
            print(f"    {i}. {edge.get('fact', 'N/A')}")
            if edge.get("valid_at"):
                print(f"       Valid from: {edge.get('valid_at')}")
            if edge.get("invalid_at"):
                print(f"       Valid until: {edge.get('invalid_at')}")

    if nodes:
        print("\n  Top Nodes:")
        for i, node in enumerate(nodes[:5], 1):
            print(f"    {i}. {node.get('name', 'N/A')}")
            if node.get("labels"):
                print(f"       Labels: {', '.join(node.get('labels', []))}")
            summary = node.get("summary", "")
            if summary:
                summary_preview = (
                    summary[:100] + "..." if len(summary) > 100 else summary
                )
                print(f"       Summary: {summary_preview}")

    if episodes:
        print("\n  Top Episodes:")
        for i, episode in enumerate(episodes[:3], 1):
            print(f"    {i}. {episode.get('name', 'N/A')}")
            print(f"       Source: {episode.get('source', 'N/A')}")

    if communities:
        print("\n  Top Communities:")
        for i, community in enumerate(communities[:3], 1):
            print(f"    {i}. {community.get('name', 'N/A')}")


async def main():
    #################################################
    # INITIALIZATION
    #################################################
    # Connect to the Neo4j Graphiti server
    # Make sure the server is running at SERVER_URL
    #################################################

    start_time = time.time()
    print(f"[{time.time() - start_time:.2f}s] Starting search test (basic, center node, advanced)")
    print(f"[{time.time() - start_time:.2f}s] Connecting to server at {SERVER_URL}")
    print(
        f"[{time.time() - start_time:.2f}s] Using LLM client: {DEFAULT_LLM_CLIENT}, Embedder client: {DEFAULT_EMBEDDER_CLIENT}"
    )

    # Increase timeout to handle LLM retries
    async with httpx.AsyncClient(timeout=300.0) as client:
        # Check server health
        health_check_start = time.time()
        try:
            health_response = await client.get(f"{SERVER_URL}/healthcheck")
            health_response.raise_for_status()
            health_check_time = time.time() - health_check_start
            print(
                f"[{time.time() - start_time:.2f}s] ✓ Server is healthy (health check took {health_check_time:.2f}s)\n"
            )
        except Exception as e:
            print(
                f"[{time.time() - start_time:.2f}s] ✗ Server health check failed: {e}"
            )
            print(f"Make sure the server is running at {SERVER_URL}")
            return

        try:
            #################################################
            # BASIC SEARCH
            #################################################
            # The simplest way to retrieve relationships (edges)
            # from Graphiti is using the search method, which
            # performs a hybrid search combining semantic
            # similarity and BM25 text retrieval.
            #################################################

            basic_search_start = time.time()
            print("=" * 60)
            print("BASIC SEARCH")
            print("=" * 60)

            # Perform a hybrid search combining semantic similarity and BM25 retrieval
            query = "Who was the California Attorney General?"
            print(f"\n[{time.time() - start_time:.2f}s] Searching for: '{query}'")
            print(
                f"[{time.time() - start_time:.2f}s] Using LLM: {DEFAULT_LLM_CLIENT}, Embedder: {DEFAULT_EMBEDDER_CLIENT}"
            )

            try:
                search_results = await basic_search(
                    client=client,
                    query=query,
                    llm_client=DEFAULT_LLM_CLIENT,
                    embedder_client=DEFAULT_EMBEDDER_CLIENT,
                    num_results=10,
                )

                basic_search_time = time.time() - basic_search_start
                print(
                    f"[{time.time() - start_time:.2f}s] ✓ Basic search completed (took {basic_search_time:.2f}s)"
                )

                # Print search results
                facts = search_results.get("facts", [])
                print(f"\nFound {len(facts)} results:")
                for i, fact in enumerate(facts[:5], 1):
                    print(f'\n{i}. UUID: {fact.get("uuid")}')
                    print(f'   Fact: {fact.get("fact")}')
                    if fact.get("valid_at"):
                        print(f'   Valid from: {fact.get("valid_at")}')
                    if fact.get("invalid_at"):
                        print(f'   Valid until: {fact.get("invalid_at")}')
                    if fact.get("source_node_uuid"):
                        print(f'   Source Node UUID: {fact.get("source_node_uuid")}')

            except Exception as e:
                basic_search_time = time.time() - basic_search_start
                print(
                    f"[{time.time() - start_time:.2f}s] ✗ Basic search failed: {str(e)} (took {basic_search_time:.2f}s)"
                )
                facts = []

            #################################################
            # CENTER NODE SEARCH
            #################################################
            # For more contextually relevant results, you can
            # use a center node to rerank search results based
            # on their graph distance to a specific node
            #################################################

            if facts and len(facts) > 0:
                center_search_start = time.time()
                print("\n" + "=" * 60)
                print("CENTER NODE SEARCH")
                print("=" * 60)

                # Get the source node UUID from the top result
                center_node_uuid = facts[0].get("source_node_uuid")

                if center_node_uuid:
                    print(
                        f"\n[{time.time() - start_time:.2f}s] Reranking search results based on graph distance:"
                    )
                    print(
                        f"[{time.time() - start_time:.2f}s] Using center node UUID: {center_node_uuid}"
                    )

                    try:
                        reranked_results = await center_node_search(
                            client=client,
                            query=query,
                            center_node_uuid=center_node_uuid,
                            llm_client=DEFAULT_LLM_CLIENT,
                            embedder_client=DEFAULT_EMBEDDER_CLIENT,
                            num_results=10,
                        )

                        center_search_time = time.time() - center_search_start
                        print(
                            f"[{time.time() - start_time:.2f}s] ✓ Center node search completed (took {center_search_time:.2f}s)"
                        )

                        # Print reranked search results
                        reranked_facts = reranked_results.get("facts", [])
                        print(f"\nFound {len(reranked_facts)} reranked results:")
                        for i, fact in enumerate(reranked_facts[:5], 1):
                            print(f'\n{i}. UUID: {fact.get("uuid")}')
                            print(f'   Fact: {fact.get("fact")}')
                            if fact.get("valid_at"):
                                print(f'   Valid from: {fact.get("valid_at")}')
                            if fact.get("invalid_at"):
                                print(f'   Valid until: {fact.get("invalid_at")}')
                    except Exception as e:
                        center_search_time = time.time() - center_search_start
                        print(
                            f"[{time.time() - start_time:.2f}s] ✗ Center node search failed: {str(e)} (took {center_search_time:.2f}s)"
                        )
                else:
                    print(
                        "No source node UUID found in results for center node search."
                    )
            else:
                print("\nNo results found in the initial search to use as center node.")

            #################################################
            # ADVANCED SEARCH TESTS
            #################################################
            # Test various queries to explore the graph
            # Uses MMR reranking (COMBINED_HYBRID_SEARCH_MMR) for better semantic relevance
            #################################################

            print("\n" + "=" * 60)
            print("ADVANCED SEARCH TESTS")
            print("=" * 60)
            print(
                f"[{time.time() - start_time:.2f}s] Testing advanced search functionality"
            )
            print(
                f"[{time.time() - start_time:.2f}s] Using MMR reranking (COMBINED_HYBRID_SEARCH_MMR)"
            )
            print(
                f"[{time.time() - start_time:.2f}s] MMR provides better semantic relevance than RRF\n"
            )

            # Test queries
            test_queries = [
                "California",
                "Who was the California Attorney General?",
                "Gavin Newsom",
                "Kamala Harris",
                "What positions did people hold in California?",
            ]

            for i, query in enumerate(test_queries, 1):
                search_start = time.time()
                print(
                    f"\n[{time.time() - start_time:.2f}s] Test {i}/{len(test_queries)}: '{query}'"
                )
                print(
                    f"[{time.time() - start_time:.2f}s] Using LLM: {DEFAULT_LLM_CLIENT}, Embedder: {DEFAULT_EMBEDDER_CLIENT}"
                )

                try:
                    results = await advanced_search(
                        client=client,
                        query=query,
                        llm_client=DEFAULT_LLM_CLIENT,
                        embedder_client=DEFAULT_EMBEDDER_CLIENT,
                        limit=10,
                    )

                    search_time = time.time() - search_start
                    print(
                        f"[{time.time() - start_time:.2f}s] ✓ Search completed (took {search_time:.2f}s)"
                    )

                    print_search_results(results, query)

                except Exception as e:
                    search_time = time.time() - search_start
                    print(
                        f"[{time.time() - start_time:.2f}s] ✗ Search failed: {str(e)} (took {search_time:.2f}s)"
                    )

            #################################################
            # ADVANCED SEARCH WITH CENTER NODE
            #################################################
            # Test advanced search with center node reranking
            # Center node adds graph context by reranking results based on
            # graph distance to a specific node, providing more contextually
            # relevant results. This is especially useful when you have a
            # specific entity/context to focus on.
            #################################################

            print("\n" + "=" * 60)
            print("ADVANCED SEARCH WITH CENTER NODE")
            print("=" * 60)
            print(
                f"[{time.time() - start_time:.2f}s] Testing center node reranking for better contextual relevance"
            )

            # First, do a search to find a node UUID to use as center
            print(f"\n[{time.time() - start_time:.2f}s] Finding a center node...")
            center_search_start = time.time()

            try:
                initial_results = await advanced_search(
                    client=client,
                    query="California",
                    llm_client=DEFAULT_LLM_CLIENT,
                    embedder_client=DEFAULT_EMBEDDER_CLIENT,
                    limit=5,
                )

                center_search_time = time.time() - center_search_start
                nodes = initial_results.get("nodes", [])

                if nodes and len(nodes) > 0:
                    center_node = nodes[0]
                    center_node_uuid = center_node.get("uuid")
                    center_node_name = center_node.get("name", "Unknown")

                    print(
                        f"[{time.time() - start_time:.2f}s] ✓ Found center node: '{center_node_name}' (UUID: {center_node_uuid}) (took {center_search_time:.2f}s)"
                    )

                    # Now search with center node
                    # This will rerank results based on graph distance to the center node,
                    # providing more contextually relevant results
                    print(
                        f"\n[{time.time() - start_time:.2f}s] Searching with center node reranking..."
                    )
                    print(
                        f"[{time.time() - start_time:.2f}s] Results will be reranked by graph distance to '{center_node_name}'"
                    )
                    center_rerank_start = time.time()

                    reranked_results = await advanced_search(
                        client=client,
                        query="California Governor",
                        llm_client=DEFAULT_LLM_CLIENT,
                        embedder_client=DEFAULT_EMBEDDER_CLIENT,
                        center_node_uuid=center_node_uuid,
                        limit=10,
                    )

                    center_rerank_time = time.time() - center_rerank_start
                    print(
                        f"[{time.time() - start_time:.2f}s] ✓ Center node search completed (took {center_rerank_time:.2f}s)"
                    )
                    print(
                        f"[{time.time() - start_time:.2f}s] Results are now contextually ranked by proximity to '{center_node_name}'"
                    )

                    print_search_results(
                        reranked_results, "California Governor (with center node)"
                    )

                else:
                    print(
                        f"[{time.time() - start_time:.2f}s] ⚠ No nodes found to use as center node"
                    )

            except Exception as e:
                print(
                    f"[{time.time() - start_time:.2f}s] ✗ Center node search failed: {str(e)}"
                )

            #################################################
            # TEST COMPLETE
            #################################################

            total_time = time.time() - start_time
            print("\n" + "=" * 60)
            print("TEST COMPLETE")
            print("=" * 60)
            print(f"[{total_time:.2f}s] Total execution time: {total_time:.2f}s")
            print("\n" + "=" * 60)
            print("SEARCH QUALITY NOTES")
            print("=" * 60)
            print("Search Types Tested:")
            print("  1. Basic Search: Hybrid search (BM25 + semantic) returning facts/edges")
            print("  2. Center Node Search: Reranks by graph distance to a center node")
            print("  3. Advanced Search: Returns nodes, edges, episodes, communities")
            print("\nAdvanced Search Configuration: MMR reranking (COMBINED_HYBRID_SEARCH_MMR)")
            print("  - Uses semantic similarity directly (better than RRF)")
            print("  - Reranks all candidates by query similarity")
            print("  - Provides better semantic relevance for answer quality")
            print("\nBest Practices:")
            print("  - Use basic search for simple fact retrieval")
            print("  - Use center node search when you have a specific entity context")
            print("  - Use advanced search for comprehensive graph exploration")
            print("  - MMR + center node = best quality (semantic relevance + graph context)")
            print("  - MMR is optimal for small result sets (< 20 candidates)")
            print("=" * 60)

        except httpx.HTTPStatusError as e:
            print(f"\n✗ HTTP Error: {e.response.status_code}")
            print(f"Response: {e.response.text}")
        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
