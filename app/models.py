"""Database models for WhatsApp chatbot session and message tracking.

Defines SQLModel classes for managing conversation sessions, user answers,
and message tracking with SQLite database backend.
"""

from typing import Optional
from sqlmodel import SQLModel, Field, create_engine, Index
from datetime import datetime

engine = create_engine("sqlite:///./whatspr.db", echo=False)


class SessionModel(SQLModel, table=True):
    """Represents a user conversation session.

    Tracks individual user sessions with phone number identification
    and completion status for conversation flow management.

    Attributes:
        id: Primary key for the session.
        phone: User's phone number in international format.
        completed: Whether the conversation session is completed.
        created_at: Timestamp when session was created.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    phone: str
    completed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Answer(SQLModel, table=True):
    """Stores user answers to press release questions.

    Links user responses to specific session and field identifiers
    for press release data collection and retrieval.

    Attributes:
        id: Primary key for the answer record.
        session_id: Foreign key reference to SessionModel.
        field: Field name/identifier for the answer.
        value: User's response value.
        created_at: Timestamp when answer was recorded.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="sessionmodel.id")
    field: str
    value: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Message(SQLModel, table=True):
    """Tracks Twilio message IDs for duplicate prevention.

    Stores message identifiers to prevent processing duplicate
    webhook calls from Twilio's retry mechanism.

    Attributes:
        id: Twilio MessageSid as primary key.
        session_id: Foreign key reference to SessionModel.
        created_at: Timestamp when message was processed.
    """

    id: str = Field(primary_key=True)  # Twilio MessageSid
    session_id: int = Field(foreign_key="sessionmodel.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


Index("ux_message_sid", Message.id, unique=True)


def init_db():
    """Initialize database tables and schema.

    Creates all SQLModel tables in the SQLite database if they don't exist.
    Safe to call multiple times as it only creates missing tables.
    """
    SQLModel.metadata.create_all(engine)
