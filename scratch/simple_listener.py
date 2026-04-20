from telethon import TelegramClient, events
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

api_id = int(os.getenv("TELEGRAM_API_ID"))
api_hash = os.getenv("TELEGRAM_API_HASH")
bot_token = os.getenv("BOT_TOKEN")

client = TelegramClient('listener_test', api_id, api_hash)

@client.on(events.NewMessage())
async def handler(event):
    print(f"\n--- RECV ---")
    if event.entities:
        for ent in event.entities:
            if hasattr(ent, 'document_id'):
                print(f"ID: {ent.document_id}")
    print("------------\n")

async def main():
    await client.start(bot_token=bot_token)
    print("READY. SEND EMOJI.")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
