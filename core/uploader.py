import os
import asyncio
from telethon import TelegramClient, events, types
from loguru import logger
from typing import Optional, Callable, Any, Coroutine

class TelegramUploader:
    def __init__(self, client: TelegramClient):
        self.client = client

    async def upload_file(
        self,
        chat_id: int,
        file_path: str,
        caption: str = "",
        progress_callback: Optional[Callable[[int, int], Coroutine]] = None
    ):
        """Upload a file to Telegram with optional progress bar updates."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_size = os.path.getsize(file_path)
        
        # Note: Telethon handles large files automatically, but splitting is often 
        # required for files > 2GB (Telegram limit for regular accounts).
        # For simplicity, we assume the file is within limits or handled by Telethon.
        
        last_percent = 0

        async def _progress(current, total):
            nonlocal last_percent
            percent = int((current / total) * 100)
            if percent > last_percent and progress_callback:
                last_percent = percent
                await progress_callback(current, total)

        logger.info(f"Uploading {file_path} ({file_size} bytes)")
        
        await self.client.send_file(
            chat_id,
            file_path,
            caption=caption,
            progress_callback=_progress if progress_callback else None,
            supports_streaming=True
        )
        
        logger.info(f"Upload complete: {file_path}")
