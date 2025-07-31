from fastapi import FastAPI
from app.agent_endpoint import router
import os

# Only include agent endpoint if AGENT_MODE is enabled
app = FastAPI()

if os.environ.get("AGENT_MODE") == "true":
    app.include_router(router)


@app.get("/")
async def root():
    if os.environ.get("AGENT_MODE") == "true":
        return {"message": "Agent mode enabled", "endpoint": "/agent"}
    else:
        return {"message": "Agent mode disabled"}
