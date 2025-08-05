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
    with current operating mode.
    """
    init_db()
    log.info("db_ready", legacy_mode=LEGACY)


if LEGACY:
    from .legacy_main import router as legacy_router

    app.include_router(legacy_router, prefix="")
else:
    from .agent_endpoint import router as agent_router

    app.include_router(agent_router, prefix="")
