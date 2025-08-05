"""Atomic tool definitions for WhatsPR.

Each tool saves a specific slot directly to the database (or any persistence backend).
All tools return a short confirmation string so the Assistant can echo success if needed.
"""

from typing import Optional
from contextlib import contextmanager
import os

# Import database components - graceful fallback if not available
try:
    from sqlmodel import Session, select
    from .models import Answer, engine

    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    print("[WARNING] Database components not available, using debug mode")


@contextmanager
def get_db_session():
    """Get database session with proper cleanup and transaction management.

    Context manager that provides a database session with automatic commit/rollback
    handling. Falls back gracefully if database components are not available.

    Yields:
        Optional[Session]: Database session or None if DB_AVAILABLE is False.

    Raises:
        Exception: Re-raises any database operation exceptions after rollback.
    """
    if not DB_AVAILABLE:
        yield None
        return

    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _save(slot: str, value: str, session_id: Optional[int] = None) -> str:
    """Internal helper function to persist field values to database.

    Saves or updates a field value for a specific session in the database.
    Provides graceful fallback to debug mode if database is unavailable.

    Args:
        slot: The field name/slot identifier to save.
        value: The value to save for this field.
        session_id: Optional session ID. Defaults to environment variable or 1.

    Returns:
        str: Confirmation message indicating save status.

    Note:
        Uses DEBUG mode fallback if database components are unavailable.
    """
    if not DB_AVAILABLE:
        # Fallback to debug mode if database not available
        print(f"[DEBUG] Saved {slot} -> {value[:50]}...")
        return f"{slot} saved (debug mode)."

    try:
        # For staging/testing, use a default session ID if none provided
        # In production, this should come from the conversation context
        if session_id is None:
            session_id = int(os.environ.get("DEFAULT_SESSION_ID", "1"))

        with get_db_session() as db:
            if db is None:
                raise Exception("Database session not available")

            # Check if this field already exists for this session
            statement = select(Answer).where(Answer.session_id == session_id, Answer.field == slot)
            existing = db.exec(statement).first()

            if existing:
                # Update existing answer
                existing.value = value
                action = "updated"
            else:
                # Create new answer
                answer = Answer(session_id=session_id, field=slot, value=value)
                db.add(answer)
                action = "saved"

            # Keep debug print for development visibility
            print(f"[DB] {action.title()} {slot} -> {value[:50]}...")

        return f"{slot} {action}."

    except Exception as e:
        # Fallback to debug mode if database fails
        print(f"[ERROR] Database save failed for {slot}: {e}")
        print(f"[DEBUG] Saved {slot} -> {value[:50]}...")
        return f"{slot} saved (debug mode)."


def save_announcement_type(value: str) -> str:
    """Save announcement type information to database.

    Args:
        value: Announcement type (e.g., "Funding round", "Product launch").

    Returns:
        str: Confirmation message that the announcement type was saved.
    """
    return _save("announcement_type", value)


def save_headline(value: str) -> str:
    """Save press release headline to database.

    Args:
        value: The press release headline text.

    Returns:
        str: Confirmation message that the headline was saved.
    """
    return _save("headline", value)


def save_key_facts(value: str) -> str:
    """Save key facts about the announcement to database.

    Args:
        value: Key facts including who, what, when, amount, investors, etc.

    Returns:
        str: Confirmation message that the key facts were saved.
    """
    return _save("key_facts", value)


def save_quotes(value: str) -> str:
    """Save relevant quotes to database.

    Args:
        value: Quotes from executives, investors, or other relevant parties.

    Returns:
        str: Confirmation message that the quotes were saved.
    """
    return _save("quotes", value)


def save_boilerplate(value: str) -> str:
    """Save company boilerplate description to database.

    Args:
        value: Standard company description paragraph for press releases.

    Returns:
        str: Confirmation message that the boilerplate was saved.
    """
    return _save("boilerplate", value)


def save_media_contact(value: str) -> str:
    """Save media contact information to database.

    Args:
        value: Media contact details including name, email, and phone number.

    Returns:
        str: Confirmation message that the media contact was saved.
    """
    return _save("media_contact", value)
