"""
Safety tests to ensure staging environment doesn't use production keys.
"""

import os
from pathlib import Path
from dotenv import load_dotenv


def test_no_production_keys_in_staging():
    """Test that staging environment doesn't contain production API keys."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    staging_env_path = project_root / ".env.staging"

    # Skip test if .env.staging doesn't exist
    if not staging_env_path.exists():
        return

    # Load the staging environment variables
    load_dotenv(staging_env_path, override=True)

    # Get the OpenAI API key
    openai_key = os.getenv("OPENAI_API_KEY", "")

    # Assert that the key doesn't contain 'prod' substring
    assert (
        "prod" not in openai_key.lower()
    ), "OPENAI_API_KEY in .env.staging contains 'prod' - this might be a production key!"
