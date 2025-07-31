from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from functools import cached_property
from typing import List, Optional


class Settings(BaseSettings):
    flow_spec_path: Path = Path("flows/pr_intake.yaml")
    twilio_auth_token: str
    openai_api_key: Optional[str] = None
    llm_enabled: bool = False  # 🔑 feature flag

    # Legacy field list for backward compatibility
    required_fields: List[str] = [
        "announcement_type",
        "headline",
        "key_facts",
        "quotes",
        "boilerplate",
        "media_contact",
    ]
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @cached_property
    def flow(self):
        try:
            from .flow_loader import load_flow

            return load_flow(str(self.flow_spec_path))
        except (ImportError, FileNotFoundError):
            # Fallback to legacy behavior if flow spec not found
            return None


settings = Settings()
