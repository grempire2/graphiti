import asyncio
import json
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


async def add_episode(
    client: httpx.AsyncClient,
    name: str,
    episode_body: str,
    source: str = "text",
    source_description: str = "",
    llm_client: str = DEFAULT_LLM_CLIENT,
    embedder_client: str = DEFAULT_EMBEDDER_CLIENT,
    group_id: str | None = None,
    uuid: str | None = None,
) -> dict:
    """Add an episode to the graph."""
    payload = {
        "name": name,
        "episode_body": episode_body,
        "source": source,
        "source_description": source_description,
        "llm_client": llm_client,
        "embedder_client": embedder_client,
    }
    if group_id:
        payload["group_id"] = group_id
    if uuid:
        payload["uuid"] = uuid

    response = await client.post(f"{API_BASE}/episodes", json=payload)
    response.raise_for_status()
    return response.json()


async def basic_search(
    client: httpx.AsyncClient,
    query: str,
    llm_client: str = DEFAULT_LLM_CLIENT,
    embedder_client: str = DEFAULT_EMBEDDER_CLIENT,
    group_ids: list[str] | None = None,
    num_results: int = 10,
) -> dict:
    """Perform a basic search."""
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
    """Perform a center node search."""
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
    """Perform an advanced search."""
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


async def main():
    #################################################
    # INITIALIZATION
    #################################################
    # Connect to the Neo4j Graphiti server
    # Make sure the server is running at SERVER_URL
    #################################################

    start_time = time.time()
    print(f"[{time.time() - start_time:.2f}s] Starting test script")
    print(f"[{time.time() - start_time:.2f}s] Connecting to server at {SERVER_URL}")
    print(
        f"[{time.time() - start_time:.2f}s] Using LLM client: {DEFAULT_LLM_CLIENT}, Embedder client: {DEFAULT_EMBEDDER_CLIENT}"
    )

    # Increase timeout to handle LLM retries (up to 4 attempts with exponential backoff)
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
            # ADDING EPISODES
            #################################################
            # Episodes are the primary units of information
            # in Graphiti. They can be text or structured JSON
            # and are automatically processed to extract entities
            # and relationships.
            #################################################

            episodes_start_time = time.time()
            print("=" * 60)
            print("ADDING EPISODES")
            print("=" * 60)
            print(f"[{time.time() - start_time:.2f}s] Starting episode addition")

            # Example: Add Episodes
            # Episodes list containing both text and JSON episodes
            episodes = [
                {
                    "content": "Kamala Harris is the Attorney General of California. She was previously "
                    "the district attorney for San Francisco.",
                    "type": "text",
                    "description": "podcast transcript",
                },
                {
                    "content": "As AG, Harris was in office from January 3, 2011 – January 3, 2017",
                    "type": "text",
                    "description": "podcast transcript",
                },
                {
                    "content": {
                        "name": "Gavin Newsom",
                        "position": "Governor",
                        "state": "California",
                        "previous_role": "Lieutenant Governor",
                        "previous_location": "San Francisco",
                    },
                    "type": "json",
                    "description": "podcast metadata",
                },
                {
                    "content": {
                        "name": "Gavin Newsom",
                        "position": "Governor",
                        "term_start": "January 7, 2019",
                        "term_end": "Present",
                    },
                    "type": "json",
                    "description": "podcast metadata",
                },
            ]

            # Add episodes to the graph
            episode_uuids = []
            for i, episode in enumerate(episodes):
                episode_body = (
                    episode["content"]
                    if isinstance(episode["content"], str)
                    else json.dumps(episode["content"])
                )

                episode_start = time.time()
                print(
                    f"[{time.time() - start_time:.2f}s] Adding episode {i} ({episode['type']})..."
                )

                result = await add_episode(
                    client=client,
                    name=f"Freakonomics Radio {i}",
                    episode_body=episode_body,
                    source=episode["type"],
                    source_description=episode["description"],
                    llm_client=DEFAULT_LLM_CLIENT,
                    embedder_client=DEFAULT_EMBEDDER_CLIENT,
                )

                episode_time = time.time() - episode_start
                if result.get("success"):
                    episode_uuid = result.get("episode_uuid")
                    episode_uuids.append(episode_uuid)
                    print(
                        f'[{time.time() - start_time:.2f}s] ✓ Added episode: Freakonomics Radio {i} ({episode["type"]}) - UUID: {episode_uuid} (took {episode_time:.2f}s)'
                    )
                else:
                    print(
                        f'[{time.time() - start_time:.2f}s] ✗ Failed to add episode {i}: {result.get("message")} (took {episode_time:.2f}s)'
                    )

            episodes_total_time = time.time() - episodes_start_time
            print(
                f"\n[{time.time() - start_time:.2f}s] Added {len(episode_uuids)} episodes successfully (total time: {episodes_total_time:.2f}s, avg: {episodes_total_time/len(episodes) if episodes else 0:.2f}s per episode)\n"
            )

            # Wait a bit for episodes to be processed
            # print("Waiting for episodes to be processed...")
            # await asyncio.sleep(5)

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

            search_results = await basic_search(
                client=client,
                query=query,
                llm_client=DEFAULT_LLM_CLIENT,
                embedder_client=DEFAULT_EMBEDDER_CLIENT,
                num_results=10,
            )

            basic_search_time = time.time() - basic_search_start
            print(
                f"[{time.time() - start_time:.2f}s] Basic search completed (took {basic_search_time:.2f}s)"
            )

            # Print search results
            facts = search_results.get("facts", [])
            print(f"\nFound {len(facts)} results:")
            for i, fact in enumerate(facts, 1):
                print(f'\n{i}. UUID: {fact.get("uuid")}')
                print(f'   Fact: {fact.get("fact")}')
                if fact.get("valid_at"):
                    print(f'   Valid from: {fact.get("valid_at")}')
                if fact.get("invalid_at"):
                    print(f'   Valid until: {fact.get("invalid_at")}')
                if fact.get("source_node_uuid"):
                    print(f'   Source Node UUID: {fact.get("source_node_uuid")}')

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
                        f"[{time.time() - start_time:.2f}s] Center node search completed (took {center_search_time:.2f}s)"
                    )

                    # Print reranked search results
                    reranked_facts = reranked_results.get("facts", [])
                    print(f"\nFound {len(reranked_facts)} reranked results:")
                    for i, fact in enumerate(reranked_facts, 1):
                        print(f'\n{i}. UUID: {fact.get("uuid")}')
                        print(f'   Fact: {fact.get("fact")}')
                        if fact.get("valid_at"):
                            print(f'   Valid from: {fact.get("valid_at")}')
                        if fact.get("invalid_at"):
                            print(f'   Valid until: {fact.get("invalid_at")}')
                else:
                    print(
                        "No source node UUID found in results for center node search."
                    )
            else:
                print("\nNo results found in the initial search to use as center node.")

            #################################################
            # ADVANCED SEARCH
            #################################################
            # Graphiti provides advanced search using search_()
            # that returns nodes, edges, episodes, and communities
            #################################################

            print("\n" + "=" * 60)
            print("ADVANCED SEARCH")
            print("=" * 60)

            # Example: Perform an advanced search
            advanced_query = "California Governor"
            print(f'\nPerforming advanced search for: "{advanced_query}"')
            print(
                f"Using LLM: {DEFAULT_LLM_CLIENT}, Embedder: {DEFAULT_EMBEDDER_CLIENT}"
            )

            advanced_results = await advanced_search(
                client=client,
                query=advanced_query,
                llm_client=DEFAULT_LLM_CLIENT,
                embedder_client=DEFAULT_EMBEDDER_CLIENT,
                limit=5,
            )

            # Print advanced search results
            edges = advanced_results.get("edges", [])
            nodes = advanced_results.get("nodes", [])
            episodes = advanced_results.get("episodes", [])
            communities = advanced_results.get("communities", [])

            print(f"\nAdvanced Search Results:")
            print(f"  Edges: {len(edges)}")
            print(f"  Nodes: {len(nodes)}")
            print(f"  Episodes: {len(episodes)}")
            print(f"  Communities: {len(communities)}")

            if nodes:
                print("\nNodes:")
                for i, node in enumerate(nodes[:5], 1):
                    print(f'\n{i}. UUID: {node.get("uuid")}')
                    print(f'   Name: {node.get("name")}')
                    summary = node.get("summary", "")
                    if summary:
                        summary_preview = (
                            summary[:100] + "..." if len(summary) > 100 else summary
                        )
                        print(f"   Summary: {summary_preview}")
                    if node.get("labels"):
                        print(f'   Labels: {", ".join(node.get("labels", []))}')

            if edges:
                print("\nEdges:")
                for i, edge in enumerate(edges[:5], 1):
                    print(f'\n{i}. UUID: {edge.get("uuid")}')
                    print(f'   Fact: {edge.get("fact")}')

            #################################################
            # TEST COMPLETE
            #################################################

            total_time = time.time() - start_time
            print("\n" + "=" * 60)
            print("TEST COMPLETE")
            print("=" * 60)
            print(f"[{total_time:.2f}s] Total execution time: {total_time:.2f}s")

        except httpx.HTTPStatusError as e:
            print(f"\n✗ HTTP Error: {e.response.status_code}")
            print(f"Response: {e.response.text}")
        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
