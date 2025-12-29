import httpx
import asyncio

BASE_URL = "http://localhost:18888"


async def search():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Search for the facts
        search_queries = [
            "Who was the California Attorney General?",
            "Who is the Governor of California?",
        ]

        for query in search_queries:
            print(f"\nSearching for: '{query}'")
            search_request = {
                "query": query,
                "group_ids": ["test_group"],
                "max_facts": 5,
                "embedding_mode": "quality",
            }

            response = await client.post(f"{BASE_URL}/search", json=search_request)

            if response.status_code == 200:
                results = response.json()
                print("Search Results:")
                facts = results.get("facts", [])
                if not facts:
                    print("No facts found.")
                for fact in facts:
                    print(f"- Fact: {fact['fact']}")
                    print(f"  UUID: {fact['uuid']}")
            else:
                print(
                    f"Search failed with status {response.status_code}: {response.text}"
                )


if __name__ == "__main__":
    asyncio.run(search())
