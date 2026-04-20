from telethon import TelegramClient, events, functions, types
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

api_id = int(os.getenv("TELEGRAM_API_ID"))
api_hash = os.getenv("TELEGRAM_API_HASH")
bot_token = os.getenv("BOT_TOKEN")

client = TelegramClient('emoji_resolver', api_id, api_hash)

async def main():
    await client.start(bot_token=bot_token)
    
    try:
        for pack in ['TajalyanEmoji', 'iconemoji1']:
            print(f"\n--- PACK: {pack} ---")
            result = await client(functions.messages.GetStickerSetRequest(
                stickerset=types.InputStickerSetShortName(short_name=pack),
                hash=0
            ))
            
            print(f"Pack Title: {result.set.title}")
            print(f"Total Emojis: {len(result.documents)}")
            
            for i, doc in enumerate(result.documents[:5]):
                print(f"Emoji {i+1} ID: {doc.id}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
