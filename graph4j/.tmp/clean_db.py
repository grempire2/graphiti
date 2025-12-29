import httpx
import asyncio


async def clean_db():
    url = "http://localhost:18888/clear"
    print(f"Sending clear request to: {url}")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url)

            if response.status_code == 200:
                result = response.json()
                print(f"SUCCESS: {result.get('message', 'Database cleared')}")
            else:
                print(
                    f"ERROR: Failed to clean database. Status: {response.status_code}"
                )
                print(f"Response: {response.text}")

    except httpx.ConnectError:
        print(
            "ERROR: Could not connect to the Graph4j server. Is it running on port 18888?"
        )
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(clean_db())
