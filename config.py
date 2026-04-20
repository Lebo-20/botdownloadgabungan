import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from pydantic import field_validator

load_dotenv()

class Settings(BaseSettings):
    telegram_api_id: int
    telegram_api_hash: str
    bot_token: str
    admin_ids: str # Stored as comma-separated string
    
    ffmpeg_path: str = "ffmpeg"
    aria2c_path: str = "aria2c"
    download_dir: str = "downloads"
    token_dramabos: str = ""
    token_sapimu: str = ""
    
    max_concurrent_tasks: int = 2

    # Allow loading from environment variables (case-insensitive)
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def admin_list(self) -> List[int]:
        return [int(x.strip()) for x in self.admin_ids.split(",") if x.strip()]

settings = Settings()

# Ensure download directory exists
os.makedirs(settings.download_dir, exist_ok=True)
