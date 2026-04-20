import asyncio
import os
import re
import time
from loguru import logger
from typing import List, Optional, Callable

class VideoProcessor:
    def __init__(self, ffmpeg_path: str = "ffmpeg", aria2c_path: str = "aria2c"):
        self.ffmpeg_path = ffmpeg_path
        self.aria2c_path = aria2c_path

    async def _run_ffmpeg_with_progress(self, args: List[str], on_progress: Optional[Callable] = None):
        cmd = [self.ffmpeg_path] + args
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # FFmpeg reports progress to stderr
        duration_sec = 0
        while True:
            line = await process.stderr.readline()
            if not line:
                break
            
            line_str = line.decode('utf-8', errors='ignore')
            
            # Try to find Duration
            if "Duration:" in line_str:
                match = re.search(r"Duration: (\d+):(\d+):(\d+.\d+)", line_str)
                if match:
                    h, m, s = match.groups()
                    duration_sec = int(h) * 3600 + int(m) * 60 + float(s)
            
            # Try to find Progress time
            if "time=" in line_str:
                match = re.search(r"time=(\d+):(\d+):(\d+.\d+)", line_str)
                if match and duration_sec > 0:
                    h, m, s = match.groups()
                    current_sec = int(h) * 3600 + int(m) * 60 + float(s)
                    percent = min(99.9, (current_sec / duration_sec) * 100)
                    
                    if on_progress:
                        await on_progress(percent, current_sec, duration_sec)

        try:
            await process.wait()
            if process.returncode != 0:
                raise Exception(f"FFmpeg failed with code {process.returncode}")
        except asyncio.CancelledError:
            try:
                process.terminate()
                await process.wait()
            except:
                pass
            raise asyncio.CancelledError


    async def download_video(self, url: str, dest_path: str, on_progress: Optional[Callable] = None, video_key: Optional[str] = None):
        """Download video with progress tracking."""
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        is_m3u8 = ".m3u8" in url or "m3u8" in url.lower()
        
        if is_m3u8:
            source = url
            temp_manifest = None
            if video_key:
                from core.hls_proxy import HLSProxy
                try:
                    temp_manifest = await HLSProxy.process_m3u8(url, video_key)
                    source = temp_manifest
                except Exception as e:
                    logger.error(f"HLSProxy failed: {e}. Falling back to direct URL.")
            
            args = [
                "-allowed_extensions", "ALL",
                "-protocol_whitelist", "file,http,https,tcp,tls,crypto,data",
                "-i", source,
                "-c", "copy",
                "-bsf:a", "aac_adtstoasc",
                dest_path,
                "-y", "-hide_banner", "-loglevel", "info"
            ]
            try:
                await self._run_ffmpeg_with_progress(args, on_progress)
            finally:
                if temp_manifest:
                    from core.hls_proxy import HLSProxy
                    HLSProxy.cleanup(temp_manifest)
        else:
            # Added User-Agent to avoid CDN blocking aria2c
            ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            cmd = [
                self.aria2c_path,
                "--dir", os.path.dirname(dest_path),
                "--out", os.path.basename(dest_path),
                "--split", "16",
                "--max-connection-per-server", "16",
                "--allow-overwrite=true",
                f"--user-agent={ua}",
                url
            ]
            import re
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            
            while True:
                line = await process.stdout.readline()
                if not line: break
                line_str = line.decode(errors='ignore')
                
                # Parse aria2c progress: [#685514 1.2MiB/9.8MiB(12%) ...]
                match = re.search(r'\((\d+)%\)', line_str)
                if match and on_progress:
                    percent = float(match.group(1))
                    # Aria2c doesn't easily give duration, so we pass current/total as percent/100
                    await on_progress(percent, percent, 100)
            
            try:
                await process.wait()
                if process.returncode != 0:
                    logger.error(f"aria2c failed with code {process.returncode}")
            except asyncio.CancelledError:
                try:
                    process.terminate()
                    await process.wait()
                except: pass
                raise asyncio.CancelledError
        
        if not os.path.exists(dest_path) or os.path.getsize(dest_path) < 1024 * 100:
            if os.path.exists(dest_path): 
                size = os.path.getsize(dest_path)
                logger.warning(f"File too small: {size} bytes")
                os.remove(dest_path)
            raise ValueError(f"Downloaded file invalid or too small: {dest_path}")

    def generate_progress_bar(self, percent: float, length: int = 12) -> str:
        filled_len = int(length * percent // 100)
        bar = '█' * filled_len + '░' * (length - filled_len)
        return f"[{bar}] {percent:.1f}%"

    def validate_files(self, file_paths: List[str]) -> List[str]:
        valid_files = []
        for path in file_paths:
            if os.path.exists(path) and os.path.getsize(path) >= 1024 * 200:
                valid_files.append(path)
        return valid_files

    async def merge_videos(self, input_files: List[str], output_file: str, episode_count: int, on_progress: Optional[Callable] = None):
        validated_files = self.validate_files(input_files)
        # Use a unique concat file for each merge to avoid concurrency collisions
        concat_file = f"concat_{os.path.basename(output_file)}.txt"
        with open(concat_file, "w") as f:
            for file in validated_files:
                # FFmpeg concat needs forward slashes or escaped backslashes for Windows paths
                abs_path = os.path.abspath(file).replace("\\", "/")
                f.write(f"file '{abs_path}'\n")

        args = [
            "-f", "concat", "-safe", "0", "-i", concat_file,
            "-c", "copy",
            output_file, "-y"
        ]
        
        await self._run_ffmpeg_with_progress(args, on_progress)
        if os.path.exists(concat_file): os.remove(concat_file)
