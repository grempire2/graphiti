"""
Example script to test and compare results between two Neo4j servers (Fast and Quality).
Uses the Graph4j API service to compare performance and results.
"""

import asyncio
import httpx
from datetime import datetime, timezone

# Graph4j API base URL
API_BASE_URL = "http://localhost:8001"


async def main():
    async with httpx.AsyncClient(timeout=300.0) as client:
        # Test data
        test_content = (
            "The Apollo 11 mission landed the first two humans on the Moon. "
            "Neil Armstrong and Buzz Aldrin landed the Apollo Lunar Module Eagle on July 20, 1969. "
            "Armstrong became the first person to step onto the lunar surface six hours and 39 minutes later."
        )

        print("=" * 80)
        print("Graph4j Dual-Database Comparison Test")
        print("=" * 80)

        # Step 1: Add episode to both databases using dual mode
        print("\n[1] Adding test episode to both databases (dual mode)...")
        episode_data = {
            "episodes": [
                {
                    "name": "Apollo 11",
                    "content": test_content,
                    "episode_type": "text",
                    "source_description": "Historical space mission data",
                    "reference_time": datetime.now(timezone.utc).isoformat(),
                }
            ],
            "group_id": "test_comparison",
            "embedding_mode": "dual",  # Adds to both fast and quality databases
        }

        response = await client.post(f"{API_BASE_URL}/episodes", json=episode_data)
        if response.status_code == 202:
            print("✓ Episode queued for processing")
            # Wait for processing to complete
            print("  Waiting 30 seconds for episode processing...")
            await asyncio.sleep(30)
        else:
            print(f"✗ Failed to add episode: {response.status_code}")
            print(f"  Response: {response.text}")
            return

        # Step 2: Search query
        query = "Who was the first person on the moon?"
        print(f"\n[2] Searching for: '{query}'")
        print("-" * 80)

        # Step 3: Search in Quality database
        print("\n--- QUALITY DATABASE (Default) ---")
        quality_search = {
            "query": query,
            "group_ids": ["test_comparison"],
            "max_facts": 5,
            "embedding_mode": "quality",
        }

        start_time = datetime.now()
        response = await client.post(f"{API_BASE_URL}/search", json=quality_search)
        end_time = datetime.now()
        quality_time = (end_time - start_time).total_seconds()

        if response.status_code == 200:
            quality_results = response.json()
            print(f"Search took: {quality_time:.4f} seconds")
            print(f"Results found: {len(quality_results.get('facts', []))}")
            for i, fact in enumerate(quality_results.get("facts", [])[:3], 1):
                print(f"{i}. {fact.get('fact', 'N/A')}")
        else:
            print(f"✗ Search failed: {response.status_code}")
            quality_results = {"facts": []}

        # Step 4: Search in Fast database
        print("\n--- FAST DATABASE ---")
        fast_search = {
            "query": query,
            "group_ids": ["test_comparison"],
            "max_facts": 5,
            "embedding_mode": "fast",
        }

        start_time = datetime.now()
        response = await client.post(f"{API_BASE_URL}/search", json=fast_search)
        end_time = datetime.now()
        fast_time = (end_time - start_time).total_seconds()

        if response.status_code == 200:
            fast_results = response.json()
            print(f"Search took: {fast_time:.4f} seconds")
            print(f"Results found: {len(fast_results.get('facts', []))}")
            for i, fact in enumerate(fast_results.get("facts", [])[:3], 1):
                print(f"{i}. {fact.get('fact', 'N/A')}")
        else:
            print(f"✗ Search failed: {response.status_code}")
            fast_results = {"facts": []}

        # Step 5: Comparison Summary
        print("\n" + "=" * 80)
        print("COMPARISON SUMMARY")
        print("=" * 80)
        print(f"Quality Database:")
        print(f"  - Results: {len(quality_results.get('facts', []))}")
        print(f"  - Time: {quality_time:.4f}s")
        print(f"\nFast Database:")
        print(f"  - Results: {len(fast_results.get('facts', []))}")
        print(f"  - Time: {fast_time:.4f}s")

        if fast_time > 0:
            speedup = quality_time / fast_time
            print(
                f"\nSpeed comparison: Fast is {speedup:.2f}x {'faster' if speedup > 1 else 'slower'} than Quality"
            )

        # Compare top results
        quality_facts = quality_results.get("facts", [])
        fast_facts = fast_results.get("facts", [])

        if quality_facts and fast_facts:
            top_quality = quality_facts[0].get("fact", "")
            top_fast = fast_facts[0].get("fact", "")
            match = "YES" if top_quality == top_fast else "NO"
            print(f"\nTop result matches: {match}")
            if match == "NO":
                print(f"  Quality: {top_quality[:100]}...")
                print(f"  Fast: {top_fast[:100]}...")


if __name__ == "__main__":
    print("\nMake sure the graph4j service is running:")
    print("  cd d:\\Github\\graphiti\\graph4j")
    print("  docker-compose up -d")
    print("\nStarting comparison...\n")

    asyncio.run(main())
