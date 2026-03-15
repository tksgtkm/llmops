from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    openai_api_key: str
    openai_api_base: str
    openai_model: str

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"), 
        extra="ignore"
    )