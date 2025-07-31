#!/usr/bin/env python3
import os
from pathlib import Path
from openai import OpenAI

# Load environment variables from .env file
env_file = Path(".env")
if env_file.exists():
    for line in env_file.read_text().strip().split('\n'):
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            os.environ[key] = value

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
PROMPT = Path("prompts/assistant.txt").read_text()

def create_assistant():
    try:
        # Try to get existing assistant
        assistants = client.beta.assistants.list()
        for assistant in assistants.data:
            if assistant.name == "whatspr-agent":
                print(f"Assistant already exists: {assistant.id}")
                return assistant.id
                
        # Create new assistant
        assistant = client.beta.assistants.create(
            name="whatspr-agent",
            instructions=PROMPT,
            model="gpt-4o-mini",
            tools=[
                {"type": "function", "function": {
                    "name": "save_slot",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "value": {"type": "string"}
                        },
                        "required": ["name", "value"]
                    }
                }},
                {"type": "function", "function": {
                    "name": "get_slot",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"}
                        },
                        "required": ["name"]
                    }
                }},
                {"type": "function", "function": {
                    "name": "finish",
                    "parameters": {"type": "object", "properties": {}}
                }}
            ]
        )
        print(f"Created new assistant: {assistant.id}")
        return assistant.id
    except Exception as e:
        print(f"Error creating assistant: {e}")
        return None

if __name__ == "__main__":
    assistant_id = create_assistant()
    if assistant_id:
        print(f"Assistant ready with ID: {assistant_id}")
    else:
        print("Failed to create assistant")
