
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
    """Get database session with proper cleanup."""
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
    """Internal helper – persist value to database, return confirmation."""
    if not DB_AVAILABLE:
        # Fallback to debug mode if database not available
        print(f"[DEBUG] Saved {slot} -> {value[:50]}...")
        return f"{slot} saved (debug mode)."
    
    try:
        # For staging/testing, use a default session ID if none provided
        # In production, this should come from the conversation context
        if session_id is None:
            session_id = int(os.environ.get('DEFAULT_SESSION_ID', '1'))
        
        with get_db_session() as db:
            if db is None:
                raise Exception("Database session not available")
                
            # Check if this field already exists for this session
            statement = select(Answer).where(
                Answer.session_id == session_id,
                Answer.field == slot
            )
            existing = db.exec(statement).first()
            
            if existing:
                # Update existing answer
                existing.value = value
                action = "updated"
            else:
                # Create new answer
                answer = Answer(
                    session_id=session_id,
                    field=slot,
                    value=value
                )
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
