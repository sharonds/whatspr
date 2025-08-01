#!/usr/bin/env python3

import openai
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

client = openai.OpenAI()

# Read the assistant prompt
prompt = Path("prompts/assistant.txt").read_text()

# Update the assistant with validator tool
assistant = client.beta.assistants.update(
    assistant_id="asst_5MmNyeVDUeYi3RnbX0jCuSpU",
    name="WhatsApp PR Agent",
    instructions=prompt,
    model="gpt-4o-mini",
    tools=[
        {
            "type": "function",
            "function": {
                "name": "save_slot",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "value": {"type": "string"},
                    },
                    "required": ["name", "value"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_slot",
                "parameters": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "validate",
                "description": "Validate input data like email addresses, money amounts, etc.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "The field name being validated"},
                        "value": {"type": "string", "description": "The value to validate"},
                        "rule": {
                            "type": "string",
                            "description": "The validation rule (email, money, free)",
                        },
                    },
                    "required": ["name", "value", "rule"],
                },
            },
        },
        {
            "type": "function",
            "function": {"name": "finish", "parameters": {"type": "object", "properties": {}}},
        },
    ],
)

print(f"Assistant updated: {assistant.id}")
print(
    f"Tools: {[tool.function.name if hasattr(tool, 'function') else tool.type for tool in assistant.tools]}"
)
