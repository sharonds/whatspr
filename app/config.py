from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    openai_api_key: str
    twilio_auth_token: str
    notion_token: str
    parent_page_id: str
    required_fields: List[str] = [
        "announcement_type",
        "headline",
        "key_facts",
        "quotes",
        "boilerplate",
        "media_contact",
    ]

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

settings = Settings()  # Singleton