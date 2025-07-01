import asyncio, logging, ssl, certifi, aiohttp, os
from nio import AsyncClient, MatrixRoom, RoomMessageText
from nio.responses import LoginResponse

logging.basicConfig(level=logging.INFO)

ssl_context = ssl.create_default_context(cafile=certifi.where())
client = AsyncClient("https://matrix.org", "@botmatrix123:matrix.org", ssl=ssl_context)
SYNC_TOKEN_FILE = "sync_token.txt"

# --- Message Callback ---
async def message_callback(room: MatrixRoom, event: RoomMessageText) -> None:
    if event.sender == client.user_id:
        return  # Avoid replying to self

    message = event.body
    result = await process_message(message)
    print(result)
    formatted = format_result(result)
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

    headers = list(result[0].keys())
    col_widths = {h: max(len(h), *(len(str(row.get(h, ''))) for row in result)) for h in headers}
    
    header_row = " | ".join(f"{h:<{col_widths[h]}}" for h in headers)
    separator = "-+-".join("-" * col_widths[h] for h in headers)

    data_rows = []
    
    for row in result:
        data_rows.append(" | ".join(f"{str(row.get(h, '')):<{col_widths[h]}}" for h in headers))

    table = [header_row, separator] + data_rows
    return "```\n" + "\n".join(table) + "\n```"


# --- Query AI + DB ---
async def process_message(message: str):
    async with aiohttp.ClientSession() as session:
        async with session.get("http://db-service:8003/schema") as resp:
            schema_json = await resp.json()

        ai_payload = {
            "question": message,
            "schema": schema_json
        }
        async with session.post("http://ai-service:8002/ai", json=ai_payload) as ai_resp:
            ai_data = await ai_resp.json()
            query = ai_data.get("response")

        query_payload = {"query": query}
        async with session.post("http://db-service:8003/query", json=query_payload) as query_resp:
            result = await query_resp.json()

        return result

# --- Main ---
async def main():
    client.add_event_callback(message_callback, RoomMessageText)

    print("🔐 Logging in...")
    login_response = await client.login("qymmib-diqpyp-Nevxo5")

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
