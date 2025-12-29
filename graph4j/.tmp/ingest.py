import httpx
import json
import asyncio

BASE_URL = "http://localhost:18888"


async def ingest():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Clear existing data
        # print("Cleaning up existing data...")
        # try:
        #     response = await client.post(f"{BASE_URL}/clear")
        #     print(f"Clear status: {response.status_code}, {response.json()}")
        # except Exception as e:
        #     print(f"Failed to clear data (is server running?): {e}")
        #     return

        # 2. Prepare episodes
        episodes = [
            {
                "name": "Kamala Harris Info 1",
                "content": "Kamala Harris is the Attorney General of California. She was previously the district attorney for San Francisco.",
                "episode_type": "text",
                "source_description": "podcast transcript",
            },
            {
                "name": "Kamala Harris Info 2",
                "content": "As AG, Harris was in office from January 3, 2011 – January 3, 2017",
                "episode_type": "text",
                "source_description": "podcast transcript",
            },
            {
                "name": "Gavin Newsom Meta 1",
                "content": json.dumps(
                    {
                        "name": "Gavin Newsom",
                        "position": "Governor",
                        "state": "California",
                        "previous_role": "Lieutenant Governor",
                        "previous_location": "San Francisco",
                    }
                ),
                "episode_type": "json",
                "source_description": "podcast metadata",
            },
            {
                "name": "Gavin Newsom Meta 2",
                "content": json.dumps(
                    {
                        "name": "Gavin Newsom",
                        "position": "Governor",
                        "term_start": "January 7, 2019",
                        "term_end": "Present",
                    }
                ),
                "episode_type": "json",
                "source_description": "podcast metadata",
            },
        ]

        # 3. Add episodes
        print("\nIngesting episodes...")
        ingest_request = {
            "group_id": "test_group",
            "episodes": episodes,
            "embedding_mode": "dual",
        }

        response = await client.post(f"{BASE_URL}/episodes", json=ingest_request)
        print(f"Ingest status: {response.status_code}")
        print(f"Response: {response.json()}")


if __name__ == "__main__":
    asyncio.run(ingest())
