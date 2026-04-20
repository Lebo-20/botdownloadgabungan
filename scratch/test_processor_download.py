import asyncio
import os
import sys

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.processor import VideoProcessor
from loguru import logger

async def test_processor():
    processor = VideoProcessor()
    url = "https://thwztvideo.dramaboxdb.com/04/4x2/42x3/423x9/42390000024/700597840_2/700597840.720p.narrowv3.mp4"
    dest = "downloads/test_processor_res.mp4"
    
    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    print(f"--- TESTING VideoProcessor.download_video ---")
    
    async def progress_cb(percent, current, total):
        # Use ASCII for local testing to avoid charmap errors on Windows
        filled_len = int(12 * percent // 100)
        bar = '#' * filled_len + '-' * (12 - filled_len)
        print(f"\rProgress: [{bar}] ({percent:.1f}%)", end="", flush=True)

    try:
        await processor.download_video(url, dest, on_progress=progress_cb)
        print(f"\n[OK] Download finished: {dest}")
        print(f"Size: {os.path.getsize(dest)} bytes")
    except Exception as e:
        print(f"\n[FAIL] Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_processor())
