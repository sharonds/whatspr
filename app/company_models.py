from typing import Optional
from sqlmodel import SQLModel, Field, create_engine, Relationship
from datetime import datetime

engine = create_engine("sqlite:///./whatspr.db", echo=False)

class Company(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str | None = None
    boilerplate: str | None = None
    media_email: str | None = None
    media_phone: str | None = None
    founders: list["Founder"] = Relationship(back_populates="company")

class Founder(SQLModel, table=True):
    phone: str = Field(primary_key=True)
    company_id: Optional[int] = Field(default=None, foreign_key="company.id")
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    company: Optional[Company] = Relationship(back_populates="founders")

# existing SessionModel, Answer, Message imported via existing models.py; to be merged.