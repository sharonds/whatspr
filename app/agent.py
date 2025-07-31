from openai import OpenAI
from pathlib import Path
import json, logging, os

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
PROMPT = Path("prompts/assistant.txt").read_text()

def create_thread():
    return client.beta.threads.create()

def run_thread(thread_id: str, user_msg: str):
    client.beta.threads.messages.create(thread_id, role="user", content=user_msg)
    run = client.beta.threads.runs.create(
        thread_id, assistant="whatspr-agent", instructions=PROMPT,
        tools=[{"type":"function","function":{
            "name":"save_slot","parameters":{"type":"object","properties":{"name":{"type":"string"},"value":{"type":"string"}},"required":["name","value"]}}},
               {"type":"function","function":{"name":"get_slot","parameters":{"type":"object","properties":{"name":{"type":"string"}},"required":["name"]}}},
               {"type":"function","function":{"name":"finish","parameters":{"type":"object","properties":{}}}}]
    )
    while run.status!="completed":
        run = client.beta.threads.runs.retrieve(run.thread_id, run.id)
    msgs = client.beta.threads.messages.list(thread_id)
    return msgs.data[0].content[0].text.value