import asyncio, logging, ssl, certifi, aiohttp
from nio import AsyncClient, MatrixRoom, RoomMessageText
from nio.responses import LoginResponse

logging.basicConfig(level=logging.DEBUG)

# SSL context using certifi's CA bundle
ssl_context = ssl.create_default_context(cafile=certifi.where())

client = AsyncClient("https://matrix.org", "@botmatrix123:matrix.org", ssl=ssl_context)

async def message_callback(room: MatrixRoom, event: RoomMessageText) -> None:
    message = event.body
    result = await process_message(message) 
    
    formatted_result = format_result(result)
    await send_message(room.room_id, formatted_result)  

async def send_message(room_id: str, message: str):
    await client.room_send(
        room_id=room_id,
        message_type="m.room.message",
        content={
            "msgtype": "m.text",
            "body": message
        }
    )

def format_result(result: list[dict]) -> str:
    print(result)
    if not result:
        return "No results found."
    
    output = []
    for i, row in enumerate(result, start=1):
        output.append(f"Result #{i}:")
        for key, value in row.items():
            output.append(f"  • {key}: {value}")
        output.append("") 

    return "\n".join(output)

async def process_message(message: str):
    async with aiohttp.ClientSession() as session:
        # Step 1: Get schema
        async with session.get("http://db-service:8003/schema") as resp:
            schema_json = await resp.json()

        # Step 2: Send to AI microservice
        ai_payload = {
            "question": message,
            "schema": schema_json
        }
        async with session.post("http://ai-service:8002/ai", json=ai_payload) as ai_resp:
            ai_data = await ai_resp.json()
            query = ai_data.get("query")

        # Step 3: Query the DB
        query_payload = {"query": query}
        async with session.post("http://db-service:8003/query", json=query_payload) as query_resp:
            result = await query_resp.json()

        return result

async def main() -> None:
    client.add_event_callback(message_callback, RoomMessageText)

    print("🔐 Logging in...")
    login_response = await client.login("qymmib-diqpyp-Nevxo5")

    if isinstance(login_response, LoginResponse):
        print("✅ Login success")
    else:
        print("❌ Login failed")
        return

    await client.sync_forever(timeout=30000)

if __name__ == "__main__":
    asyncio.run(main())
