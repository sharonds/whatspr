from typing import Optional
from sqlmodel import SQLModel, Field, create_engine, Index
from datetime import datetime

engine = create_engine("sqlite:///./whatspr.db", echo=False)


class SessionModel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    phone: str
    completed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Answer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="sessionmodel.id")
    field: str
    value: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Message(SQLModel, table=True):
    id: str = Field(primary_key=True)  # Twilio MessageSid
    session_id: int = Field(foreign_key="sessionmodel.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


Index("ux_message_sid", Message.id, unique=True)


def init_db():
    SQLModel.metadata.create_all(engine)
