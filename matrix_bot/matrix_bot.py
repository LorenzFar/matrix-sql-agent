import asyncio, logging, ssl, certifi, aiohttp
from nio import AsyncClient, MatrixRoom, RoomMessageText
from nio.responses import LoginResponse

logging.basicConfig(level=logging.DEBUG)

# Create SSL context using certifi's CA bundle
ssl_context = ssl.create_default_context(cafile=certifi.where())

async def message_callback(room: MatrixRoom, event: RoomMessageText) -> None:
    message = event.body
    await process_message(message)  

async def process_message(message: str):
    async with aiohttp.ClientSession() as session:
        # Step 1: Get schema from DB microservice
        async with session.get("http://localhost/schema") as resp:
            schema_json = await resp.json()

        # Step 2: Send question + schema to AI microservice
        ai_payload = {
            "question": message,
            "schema": schema_json
        }
        async with session.post("http://localhost/ai", json=ai_payload) as ai_resp:
            ai_data = await ai_resp.json()
            query = ai_data.get("query")

        # Step 3: Run the query on the DB microservice
        query_payload = {"query": query}
        async with session.post("http://localhost/query", json=query_payload) as query_resp:
            result = await query_resp.json()

        return result

async def main() -> None:
    # Pass ssl=ssl_context when creating the AsyncClient
    client = AsyncClient("https://matrix.org", "@botmatrix123:matrix.org", ssl=ssl_context)

    client.add_event_callback(message_callback, RoomMessageText)

    # Login
    print("🔐 Logging in...")
    login_response = await client.login("qymmib-diqpyp-Nevxo5")
    # print(f"Login response: {login_response}")

    if isinstance(login_response, LoginResponse):
        print("✅ Login success")
    else:
        print("❌ Login failed")
        return

    # Sync for replies
    await client.sync_forever(timeout=30000)

if __name__ == "__main__":
    asyncio.run(main())
