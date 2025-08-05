"""Company data models for business information storage.

Defines SQLModel classes for storing company and founder information
related to press release data collection.
"""

from typing import Optional, List
from sqlmodel import SQLModel, Field, create_engine, Relationship
from datetime import datetime

engine = create_engine("sqlite:///./whatspr.db", echo=False)


class Company(SQLModel, table=True):
    """Company information model.

    Attributes:
        id: Primary key for company record.
        name: Company name.
        boilerplate: Standard company description.
        media_email: Media contact email address.
        media_phone: Media contact phone number.
        founders: Related founder records.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = None
    boilerplate: Optional[str] = None
    media_email: Optional[str] = None
    media_phone: Optional[str] = None
    founders: List["Founder"] = Relationship(back_populates="company")


class Founder(SQLModel, table=True):
    """Founder information linked to companies.

    Attributes:
        phone: Founder's phone number as primary key.
        company_id: Foreign key to company record.
        last_seen: Timestamp of last interaction.
        company: Related company record.
    """

    phone: str = Field(primary_key=True)
    company_id: Optional[int] = Field(default=None, foreign_key="company.id")
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    company: Optional[Company] = Relationship(back_populates="founders")


# existing SessionModel, Answer, Message imported via existing models.py; to be merged.
