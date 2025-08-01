#!/usr/bin/env python3
"""
Setup script for creating a new OpenAI Assistant for staging environment.
Loads configuration from .env.staging and saves the assistant ID to .assistant_id.staging
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI


def main():
    # Get the project root directory (parent of scripts directory)
    project_root = Path(__file__).parent.parent

    # Load environment variables from .env.staging
    env_path = project_root / '.env.staging'
    if not env_path.exists():
        print(f"Error: {env_path} file not found!")
        sys.exit(1)

    load_dotenv(env_path)

    # Get OpenAI API key from environment
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY not found in .env.staging!")
        sys.exit(1)

    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)

    try:
        # Create new assistant
        assistant = client.beta.assistants.create(
            name="WhatsPR Staging Assistant",
            instructions="You are a helpful WhatsApp chatbot assistant for testing and staging purposes.",
            model="gpt-4-turbo-preview",
            tools=[],
        )

        print(f"Successfully created assistant: {assistant.name}")
        print(f"Assistant ID: {assistant.id}")

        # Save assistant ID to file
        assistant_id_path = project_root / '.assistant_id.staging'
        with open(assistant_id_path, 'w') as f:
            f.write(assistant.id)

        print(f"Assistant ID saved to: {assistant_id_path}")

    except Exception as e:
        print(f"Error creating assistant: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
