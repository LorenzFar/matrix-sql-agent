import asyncio, logging, ssl, certifi, aiohttp, os
from aiohttp import ClientError
from nio import AsyncClient, MatrixRoom, RoomMessageText
from nio.responses import LoginResponse

logging.basicConfig(level=logging.INFO)

bot_username = os.getenv("MATRIX_USERNAME")
bot_password = os.getenv("MATRIX_PASSWORD")
base_url = os.getenv("BASE_URL")

ssl_context = ssl.create_default_context(cafile=certifi.where())
client = AsyncClient(base_url, bot_username , ssl=ssl_context)
SYNC_TOKEN_FILE = "sync_token.txt"

# --- Message Callback ---
async def message_callback(room: MatrixRoom, event: RoomMessageText) -> None:
    if event.sender == client.user_id:
        return  # Avoid replying to self

    message = event.body
    result = await process_message(message)

    formatted = format_result(result)
    print(formatted)
    await send_message(room.room_id, formatted)

# --- Send Message ---
async def send_message(room_id: str, message: str):
    await client.room_send(
        room_id=room_id,
        message_type="m.room.message",
        content={
            "msgtype": "m.text",
            "body": message
        }
    )

# --- Format Result ---
def format_result(result: list[dict]) -> str:
    if not result:
        return "No results found."

    if isinstance(result, dict) and "error" in result:
        return result["error"]

    lines = []
    for i, row in enumerate(result, 1):
        lines.append(f"--- Row {i} ---")
        for key, value in row.items():
            lines.append(f"{key}: {value}")
        lines.append("")

    return "\n" + "\n".join(lines) + "\n"

# --- Query AI + DB ---
async def process_message(message: str):
    try:
        async with aiohttp.ClientSession() as session:
            # Step 1: Get schema
            try:
                async with session.get("http://db-service:8003/schema") as resp:
                    if resp.status != 200:
                        return {"error": "Failed to fetch schema."}
                    schema_json = await resp.json()
            except ClientError:
                return {"error": "Database service is unreachable (schema)."}

            # Step 2: Get AI-generated query
            ai_payload = {"question": message, "schema": schema_json}
            try:
                async with session.post("http://ai-service:8002/ai", json=ai_payload) as ai_resp:
                    if ai_resp.status != 200:
                        return {"error": "AI service failed to generate query."}
                    ai_data = await ai_resp.json()
                    query = ai_data.get("response")
                    if not query:
                        return {"error": "AI service returned no query."}
            except ClientError:
                return {"error": "AI service is unreachable."}

            # Step 3: Execute query
            query_payload = {"query": query}
            try:
                async with session.post("http://db-service:8003/query", json=query_payload) as query_resp:
                    if query_resp.status != 200:
                        return {"error": query_resp.detail}
                    result = await query_resp.json()
                    return result
            except ClientError:
                return {"error": "Database service is unreachable (query)."}

    except Exception as e:
        return {"error": "Unexpected error occurred."}

# --- Main ---
async def main():
    client.add_event_callback(message_callback, RoomMessageText)

    print("🔐 Logging in...")
    login_response = await client.login(bot_password)

    if isinstance(login_response, LoginResponse):
        print("✅ Login success")
    else:
        print("❌ Login failed")
        return

    # Load sync token if available
    if os.path.exists(SYNC_TOKEN_FILE):
        with open(SYNC_TOKEN_FILE, "r") as f:
            client.next_batch = f.read().strip()

    try:
        while True:
            sync_response = await client.sync(timeout=30000)
            if sync_response.next_batch:
                with open(SYNC_TOKEN_FILE, "w") as f:
                    f.write(sync_response.next_batch)
    except KeyboardInterrupt:
        print("🛑 Stopping bot...")
    finally:
        await client.close()
        print("✅ Cleaned up and disconnected.")

# --- Entry Point ---
if __name__ == "__main__":
    asyncio.run(main())
