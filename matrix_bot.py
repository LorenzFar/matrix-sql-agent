import asyncio, json
from nio import AsyncClient, MatrixRoom, RoomMessageText, RoomSendResponse
from nio.responses import LoginResponse
import logging
import ssl
import certifi

logging.basicConfig(level=logging.DEBUG)

# Create SSL context using certifi's CA bundle
ssl_context = ssl.create_default_context(cafile=certifi.where())

async def message_callback(room: MatrixRoom, event: RoomMessageText) -> None:
    message_data = {
        "room_id": room.room_id,
        "room_name": room.display_name,
        "sender": event.sender,
        "sender_display_name": room.user_name(event.sender),
        "message": event.body,
        "event_id": event.event_id,
        "timestamp": event.server_timestamp
    }

    print("📥 New message (JSON):")
    print(json.dumps(message_data, indent=2))

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
