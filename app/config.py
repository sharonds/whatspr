"""Application configuration management using Pydantic settings.

Handles environment variable loading, feature flags, and flow specification
configuration for the WhatsApp chatbot application.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from functools import cached_property
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings with environment variable support.

    Manages configuration for Twilio integration, OpenAI API access,
    feature flags, and conversation flow specifications.

    Attributes:
        flow_spec_path: Path to YAML flow specification file.
        twilio_auth_token: Twilio authentication token for webhook validation.
        openai_api_key: OpenAI API key for AI assistant integration.
        llm_enabled: Feature flag for LLM-powered question rephrasing.
        adv_validation: Feature flag for advanced input validation.
        required_fields: Legacy field list for backward compatibility.
    """

    flow_spec_path: Path = Path("flows/pr_intake.yaml")
    twilio_auth_token: Optional[str] = None  # Made optional for test environments
    openai_api_key: Optional[str] = None
    llm_enabled: bool = False  # 🔑 feature flag
    adv_validation: bool = False  # 🔑 advanced validation feature flag

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
        """Load conversation flow specification from YAML file.

        Returns:
            Optional[dict]: Parsed flow specification or None if not available.
        """
        try:
            from .flow_loader import load_flow

            return load_flow(str(self.flow_spec_path))
        except (ImportError, FileNotFoundError):
            # Fallback to legacy behavior if flow spec not found
            return None


settings = Settings()
