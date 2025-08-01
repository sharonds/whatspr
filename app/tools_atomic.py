
"""Atomic tool definitions for WhatsPR.

Each tool saves a specific slot directly to the database (or any persistence backend).
Replace the stub `TODO` with real persistence logic.

All tools return a short confirmation string so the Assistant can echo success if needed.
"""

from typing import Any

# In real code, import your DB/session layer:
# from .models import save_answer_to_db

def _save(slot: str, value: str) -> str:
    """Internal helper – persist value, return confirmation."""
    # TODO: replace with real DB write
    print(f"[DEBUG] Saved {slot} -> {value[:50]}...")
    return f"{slot} saved."


def save_announcement_type(value: str) -> str:
    """Saves "announcement_type" – Announcement type, e.g., Funding round, Product launch."""
    return _save("announcement_type", value)


def save_headline(value: str) -> str:
    """Saves "headline" – Press‑release headline."""
    return _save("headline", value)


def save_key_facts(value: str) -> str:
    """Saves "key_facts" – Key facts (who, what, when, amount, investors)."""
    return _save("key_facts", value)


def save_quotes(value: str) -> str:
    """Saves "quotes" – Two short quotes."""
    return _save("quotes", value)


def save_boilerplate(value: str) -> str:
    """Saves "boilerplate" – Company boilerplate paragraph."""
    return _save("boilerplate", value)


def save_media_contact(value: str) -> str:
    """Saves "media_contact" – Media contact: name – email – phone."""
    return _save("media_contact", value)
