from telethon import TelegramClient, functions, types
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

api_id = int(os.getenv("TELEGRAM_API_ID"))
api_hash = os.getenv("TELEGRAM_API_HASH")
bot_token = os.getenv("BOT_TOKEN")

client = TelegramClient('reveal_session', api_id, api_hash)

async def main():
    await client.start(bot_token=bot_token)
    target_user = 5888747846 # Admin ID
    
    for pack_name in ['TajalyanEmoji', 'iconemoji1']:
        await client.send_message(target_user, f"--- REVEALING PACK: {pack_name} ---")
        
        result = await client(functions.messages.GetStickerSetRequest(
            stickerset=types.InputStickerSetShortName(short_name=pack_name),
            hash=0
        ))
        
        docs = result.documents
        # Send in groups of 10
        for i in range(0, min(50, len(docs)), 10):
            chunk = docs[i:i+10]
            text = f"Pack: {pack_name} (Items {i+1}-{i+len(chunk)})\n\n"
            for j, doc in enumerate(chunk):
                # Try to use the alt text (emoji representation) as fallback inside the tag
                alt = doc.attributes[1].alt if len(doc.attributes) > 1 else "✨"
                text += f"{i+j+1}. <emoji id={doc.id}>{alt}</emoji> (ID: `{doc.id}`)\n"
            
            await client.send_message(target_user, text, parse_mode='html')
            await asyncio.sleep(1)

    print("Emoji reveal messages sent to admin.")

if __name__ == "__main__":
    asyncio.run(main())
