import os
import re
import base64
import aiohttp
from typing import Optional
from loguru import logger

class HLSProxy:
    """
    Handles M3U8 manifest manipulation for encrypted streams.
    Inspired by the Node.js proxy logic for GoodShort.
    """
    
    @staticmethod
    async def process_m3u8(url: str, video_key: Optional[str] = None) -> str:
        """
        Downloads a manifest, injects the AES key, rewrites segments,
        and returns the path to a temporary local .m3u8 file.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={'User-Agent': 'okhttp/4.10.0'}) as resp:
                if resp.status != 200:
                    raise Exception(f"Failed to fetch m3u8: status {resp.status}")
                content = await resp.text()

        # Get base URL for segment rewriting
        base_url = url.rsplit('/', 1)[0]
        
        # 1. Inject AES key
        if video_key:
            # Replace URI="local://..." or similar with data URI
            # The key is expected to be a base64 string
            content = re.sub(
                r'URI="[^"]*"',
                f'URI="data:text/plain;base64,{video_key}"',
                content
            )
            logger.info("HLSProxy: Injected AES key into manifest")

        # 2. Rewrite segment URLs to absolute
        lines = []
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                if not line.startswith('http'):
                    # Relative path -> Absolute
                    line = f"{base_url}/{line}"
            lines.append(line)
        
        content = '\n'.join(lines)
        
        # 3. Save to a temporary file
        temp_dir = "temp_manifests"
        os.makedirs(temp_dir, exist_ok=True)
        import uuid
        temp_file = os.path.join(temp_dir, f"{uuid.uuid4()}.m3u8")
        
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(content)
            
        logger.info(f"HLSProxy: Manifest rewritten and saved to {temp_file}")
        return temp_file

    @staticmethod
    def cleanup(temp_file: str):
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass
