"""
Example script demonstrating advanced search capabilities of graph4j.

This script shows how to use the hybrid search with RRF reranking,
entity type filtering, and center node search.
"""

import asyncio
import httpx


BASE_URL = "http://localhost:8001"


async def main():
    """Run example searches demonstrating advanced features."""
    async with httpx.AsyncClient() as client:
        print("=" * 80)
        print("Graph4j Advanced Search Examples")
        print("=" * 80)
        print()

        # Example 1: Add test data using new /episodes endpoint
        print("1. Adding test data with different episode types...")
        print("-" * 80)

        response = await client.post(
            f"{BASE_URL}/episodes",
            json={
                "group_id": "demo_user",
                "episodes": [
                    {
                        "content": "I prefer dark roast coffee in the morning",
                        "episode_type": "message",  # Message type (default)
                        "role": "user",
                        "role_type": "human",
                        "name": "Coffee Preference",
                    },
                    {
                        "content": "User lives in San Francisco and works as a software engineer",
                        "episode_type": "text",  # Text type
                        "name": "User Profile",
                    },
                    {
                        "content": '{"requirement": "task management app", "features": ["calendar integration", "reminders", "collaboration"]}',
                        "episode_type": "json",  # JSON type
                        "name": "App Requirements",
                    },
                ],
            },
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()

        # Wait for processing
        print("Waiting for episode processing...")
        await asyncio.sleep(5)
        print()

        # Example 2: Advanced node search with entity type filtering
        print("2. Advanced Node Search - Searching for preferences only")
        print("-" * 80)

        response = await client.post(
            f"{BASE_URL}/search/nodes",
            json={
                "query": "what does the user like",
                "group_ids": ["demo_user"],
                "max_nodes": 5,
                "entity_types": ["Preference"],  # Filter by entity type
            },
        )
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f'Found {len(result.get("nodes", []))} nodes')
        for node in result.get("nodes", []):
            print(f'  - {node["name"]} ({node["labels"]}): {node["summary"]}')
        print()

        # Example 3: Search for locations
        print("3. Advanced Node Search - Searching for locations")
        print("-" * 80)

        response = await client.post(
            f"{BASE_URL}/search/nodes",
            json={
                "query": "where does the user live",
                "group_ids": ["demo_user"],
                "max_nodes": 5,
                "entity_types": ["Location"],  # Filter by location
            },
        )
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f'Found {len(result.get("nodes", []))} nodes')
        for node in result.get("nodes", []):
            print(f'  - {node["name"]} ({node["labels"]}): {node["summary"]}')
        print()

        # Example 4: Search for requirements
        print("4. Advanced Node Search - Searching for requirements")
        print("-" * 80)

        response = await client.post(
            f"{BASE_URL}/search/nodes",
            json={
                "query": "what does the user need",
                "group_ids": ["demo_user"],
                "max_nodes": 5,
                "entity_types": ["Requirement"],  # Filter by requirement
            },
        )
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f'Found {len(result.get("nodes", []))} nodes')
        for node in result.get("nodes", []):
            print(f'  - {node["name"]} ({node["labels"]}): {node["summary"]}')
        print()

        # Example 5: Advanced fact search
        print("5. Advanced Fact Search - Hybrid search with RRF")
        print("-" * 80)

        response = await client.post(
            f"{BASE_URL}/search/facts",
            json={
                "query": "user preferences and needs",
                "group_ids": ["demo_user"],
                "max_facts": 10,
            },
        )
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f'Found {len(result.get("facts", []))} facts')
        for fact in result.get("facts", [])[:3]:  # Show first 3
            print(f'  - {fact["fact"]}')
        print()

        # Example 6: Center node search (if we have nodes)
        print("6. Center Node Search - Reranking by graph distance")
        print("-" * 80)

        # First get a node to use as center
        response = await client.post(
            f"{BASE_URL}/search/nodes",
            json={
                "query": "user",
                "group_ids": ["demo_user"],
                "max_nodes": 1,
            },
        )

        if response.status_code == 200:
            nodes = response.json().get("nodes", [])
            if nodes:
                center_uuid = nodes[0]["uuid"]
                print(f'Using center node: {nodes[0]["name"]} ({center_uuid})')

                # Now search with center node
                response = await client.post(
                    f"{BASE_URL}/search/facts",
                    json={
                        "query": "preferences",
                        "group_ids": ["demo_user"],
                        "max_facts": 5,
                        "center_node_uuid": center_uuid,  # Rerank by distance from this node
                    },
                )
                print(f"Status: {response.status_code}")
                result = response.json()
                print(
                    f'Found {len(result.get("facts", []))} facts (reranked by distance)'
                )
                for fact in result.get("facts", [])[:3]:
                    print(f'  - {fact["fact"]}')
            else:
                print("No nodes found for center node search")
        print()

        print("=" * 80)
        print("Examples complete!")
        print("=" * 80)
        print()
        print("Key Features Demonstrated:")
        print("  ✅ Hybrid Search (BM25 + Cosine Similarity)")
        print("  ✅ RRF Reranking")
        print("  ✅ Entity Type Filtering (Preference, Location, Requirement)")
        print("  ✅ Center Node Search (graph-distance reranking)")
        print()


if __name__ == "__main__":
    print()
    print("Make sure the graph4j server is running on http://localhost:8001")
    print("Start it with: uvicorn main:app --reload --port 8001")
    print()
    input("Press Enter to continue...")
    print()

    asyncio.run(main())
