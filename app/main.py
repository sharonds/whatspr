from fastapi import FastAPI
import os
import structlog
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from .models import init_db
from .logging_config import configure_logging
from .middleware import RequestLogMiddleware

# Initialize logging and database
configure_logging()
log = structlog.get_logger("main")

LEGACY = os.getenv("LEGACY_MODE", "false").lower() == "true"

app = FastAPI(title="WhatsPR – Agent default")
app.add_middleware(RequestLogMiddleware)


@app.on_event("startup")
def _startup():
    init_db()
    log.info("db_ready", legacy_mode=LEGACY)


if LEGACY:
    from .legacy_main import router as legacy_router

    app.include_router(legacy_router, prefix="")
else:
    from .agent_endpoint import router as agent_router

    app.include_router(agent_router, prefix="")
