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

            #################################################
            # TEST COMPLETE
            #################################################

            total_time = time.time() - start_time
            print("=" * 60)
            print("TEST COMPLETE")
            print("=" * 60)
            print(f"[{total_time:.2f}s] Total execution time: {total_time:.2f}s")
            print("\nNote: Use test_advanced.py to test search functionality")

        except httpx.HTTPStatusError as e:
            print(f"\n✗ HTTP Error: {e.response.status_code}")
            print(f"Response: {e.response.text}")
        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
