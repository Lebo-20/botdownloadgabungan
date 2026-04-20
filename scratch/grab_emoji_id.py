from telethon import TelegramClient, events
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

api_id = int(os.getenv("TELEGRAM_API_ID"))
api_hash = os.getenv("TELEGRAM_API_HASH")
bot_token = os.getenv("BOT_TOKEN")

client = TelegramClient('temp_grabber', api_id, api_hash)

@client.on(events.NewMessage())
async def handler(event):
    def safe_print(text):
        print(str(text).encode('ascii', errors='replace').decode('ascii'))

    safe_print(f"\n--- NEW MESSAGE ---")
    safe_print(f"From: {event.sender_id}")
    
    if event.entities:
        for ent in event.entities:
            safe_print(f"Entity Type: {type(ent).__name__}")
            if hasattr(ent, 'document_id'):
                safe_print(f"CUSTOM EMOJI ID: {ent.document_id}")
            elif hasattr(ent, 'id'):
                safe_print(f"ID: {ent.id}")
            
    print("-------------------\n")

async def main():
    await client.start(bot_token=bot_token)
    user_id = 5888747846 # Admin User ID from metadata
    print(f"Checking last 100 messages from {user_id}...")
    
    async for msg in client.iter_messages(user_id, limit=100):
        if msg.entities:
            for ent in msg.entities:
                if hasattr(ent, 'document_id'):
                    print(f"\n--- FOUND ---")
                    print(f"CUSTOM EMOJI ID: {ent.document_id}")
                    print(f"----------------\n")

    print("Listener active...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
