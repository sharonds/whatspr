from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):
    twilio_auth_token: str
    openai_api_key: Optional[str] = None
    llm_enabled: bool = False  # 🔑 feature flag

    required_fields: List[str] = [
        "announcement_type",
        "headline",
        "key_facts",
        "quotes",
        "boilerplate",
        "media_contact",
    ]
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
