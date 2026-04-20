import httpx
import asyncio
from loguru import logger
from typing import Optional, Dict, Any

class AsyncHTTPClient:
    def __init__(self, timeout: int = 30, retries: int = 3):
        self.timeout = timeout
        self.retries = retries
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )

    async def request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> httpx.Response:
        for attempt in range(1, self.retries + 1):
            try:
                response = await self.client.request(
                    method, url, params=params, data=data, json=json, headers=headers, **kwargs
                )
                
                # Check for rate limiting or server errors
                if response.status_code in [429, 500, 502, 503, 504]:
                    logger.warning(f"Attempt {attempt}/{self.retries} failed for {url} with status {response.status_code}")
                    if attempt < self.retries:
                        wait_time = 2 ** attempt # Exponential backoff
                        await asyncio.sleep(wait_time)
                        continue
                
                response.raise_for_status()
                return response
            
            except httpx.HTTPError as e:
                resp_text = ""
                try:
                    if hasattr(e, 'response') and e.response:
                        resp_text = f" | Body: {e.response.text[:200]}"
                except: pass
                logger.error(f"HTTP Error on attempt {attempt}/{self.retries}: {e}{resp_text}")
                if attempt == self.retries:
                    raise

                await asyncio.sleep(2 ** attempt)
        
        raise httpx.HTTPError("Max retries reached")

    async def get(self, url: str, **kwargs) -> httpx.Response:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> httpx.Response:
        return await self.request("POST", url, **kwargs)

    async def download_file(self, url: str, dest_path: str):
        """Download a file from a URL to a local path."""
        async with self.client.stream("GET", url) as response:
            response.raise_for_status()
            with open(dest_path, "wb") as f:
                async for chunk in response.aiter_bytes():
                    f.write(chunk)

    async def close(self):
        await self.client.aclose()
