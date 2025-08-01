"""Minimal example: create/update Assistant with File Search enabled.

Run once after merging PR 3.

Requires env var OPENAI_API_KEY.
"""

import time, os, json
from openai import OpenAI
from pathlib import Path

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

PROMPT = Path("prompts/assistant_v2.txt").read_text().strip()
KNOW_PATH = "knowledge/press_release_requirements.txt"

# 1. upload knowledge file (or re‑use existing)
up = client.files.create(file=open(KNOW_PATH, "rb"), purpose="assistants")
print("Uploaded", up.id, up.status)

# 2. wait until processed
while True:
    f = client.files.retrieve(up.id)
    if f.status == "processed":
        break
    time.sleep(1)

# 3. create vector store and attach
vs = client.beta.vector_stores.create(name="whatspr‑knowledge")
client.beta.vector_stores.file_batches.create(vector_store_id=vs.id, file_ids=[up.id])
print("Vector store ready:", vs.id)

# 4. create / update assistant
assistant = client.beta.assistants.create(
    name="WhatsPR Staging Assistant",
    model="gpt-4o-mini",
    instructions=PROMPT,
    tools=[{"type": "file_search"}],  # other function tools added elsewhere
    tool_resources={"file_search": {"vector_store_ids": [vs.id]}},
)
print("Assistant id:", assistant.id)
