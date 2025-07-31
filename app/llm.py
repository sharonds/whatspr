from openai import OpenAI
from typing import Optional
from .config import settings

_client = None

def get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client

def rephrase_question(field: str, previous: Optional[str] = None) -> str:
    client = get_client()
    system = "You are a helpful PR strategist."
    user = (
        f"We still need the value for '{field.replace('_', ' ')}'. "
        "Write a single, friendly question—max 15 words."
    )
    if previous:
        user += f" Previous answer was: \"{previous}\"."
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.3,
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
    )
    return completion.choices[0].message.content.strip()
