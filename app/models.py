from typing import Optional
from sqlmodel import SQLModel, Field, create_engine
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

def init_db():
    SQLModel.metadata.create_all(engine)