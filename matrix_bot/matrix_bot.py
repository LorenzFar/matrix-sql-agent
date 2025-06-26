import asyncio, json, logging, ssl, certifi, aiohttp
from nio import AsyncClient, MatrixRoom, RoomMessageText
from nio.responses import LoginResponse

logging.basicConfig(level=logging.DEBUG)

# Create SSL context using certifi's CA bundle
ssl_context = ssl.create_default_context(cafile=certifi.where())

async def message_callback(room: MatrixRoom, event: RoomMessageText) -> None:
    message = event.body
    await process_message(message)  

# Call both DB microservice & AI microservice
async def process_message(message: str):
    async with aiohttp.ClientSession() as session:
        # Step 1: Get schema from DB microservice
        async with session.get("http://localhost/schema") as resp:
            schema_json = await resp.json()
            schema = convert_schema_to_string(schema_json)

        # Step 2: Generate prompt for AI microservice
        prompt = generate_prompt(schema, message)

        # Step 3: Send prompt to AI microservice
        ai_payload = {
            "model" : "deepseek-r1:7b",
            "prompt": prompt
        }
        async with session.post("http://localhost/ai", json=ai_payload) as ai_resp:
            ai_data = await ai_resp.json()
            query = ai_data.get("query")

        # Step 4: Send query to DB microservice
        query_payload = {"query": query}
        async with session.post("http://localhost/query", json=query_payload) as query_resp:
            result = await query_resp.json()

        return result

# Function to generate prompt combining external txt with schema + user question
def generate_prompt(schema: str, question: str) -> str:
    prompt_parts = []

    try:
        with open("prompt_message.txt", 'r', encoding='utf-8') as f:
            external_context = f.read().strip()
            prompt_parts.append(external_context)
    except FileNotFoundError:
        prompt_parts.append("[WARNING: Context file not found]")

    prompt_parts.append("# Database Schema:\n" + schema)
    prompt_parts.append("# User Question:\n" + question)

    return "\n\n".join(prompt_parts)

# Convert schema JSON to a human-readable string
def convert_schema_to_string(schema: dict) -> str:
    output = []
    for table, columns in schema.items():
        output.append(f"Table: {table}")
        for col in columns:
            col_line = f"  - {col['name']} ({col['type']})"
            if col.get("PK"):
                col_line += " [PK]"
            if col.get("FK"):
                col_line += f" [FK → {col['FK']}]"
            output.append(col_line)
        output.append("")  # empty line between tables
    return "\n".join(output)

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
