"""FastAPI application setup for WhatsPR WhatsApp chatbot.

Main application module that configures FastAPI, initializes database,
sets up logging, and routes between legacy and agent modes based on
environment configuration.
"""

import os
import structlog
from fastapi import FastAPI
from dotenv import load_dotenv

from .models import init_db
from .logging_config import configure_logging
from .middleware import RequestLogMiddleware

# Load environment variables first
load_dotenv()

# Initialize logging and database
configure_logging()
log = structlog.get_logger("main")

LEGACY = os.getenv("LEGACY_MODE", "false").lower() == "true"

app = FastAPI(title="WhatsPR – Agent default")
app.add_middleware(RequestLogMiddleware)


@app.on_event("startup")
def _startup():
    """Initialize application on startup.

    Sets up database tables and logs application readiness
    with current operating mode. Validates critical environment variables.
    """
    # Validate critical environment variables
    api_key = os.environ.get("OPENAI_API_KEY", "")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "")

    if not api_key or len(api_key) < 50:
        log.error("OPENAI_API_KEY not configured or invalid", key_length=len(api_key))
        print("⚠️  WARNING: OPENAI_API_KEY not properly configured!")
        print("   Please set OPENAI_API_KEY environment variable or check .env file")
        print(f"   Current length: {len(api_key)} (expected: >50)")
    else:
        log.info("openai_api_key_validated", key_length=len(api_key))
        print(f"✅ OpenAI API key configured (length: {len(api_key)})")

    if not auth_token:
        log.warning("TWILIO_AUTH_TOKEN not configured - webhook verification will fail")
        print("⚠️  WARNING: TWILIO_AUTH_TOKEN not configured!")
    else:
        print("✅ Twilio auth token configured")

    init_db()
    log.info("db_ready", legacy_mode=LEGACY)


if LEGACY:
    from .legacy_main import router as legacy_router

    app.include_router(legacy_router, prefix="")
else:
    from .agent_endpoint import router as agent_router

    app.include_router(agent_router, prefix="")
