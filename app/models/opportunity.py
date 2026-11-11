import datetime
from enum import Enum
import uuid
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class OpportunityCategoryEnum(str, Enum):
    INTERNSHIP = "internship"
    SCHOLARSHIP = "scholarship"
    FELLOWSHIP = "fellowship"
    GRADUATE_PROGRAM = "graduate_program"
    RESEARCH = "research"
    OPEN_SOURCE = "open_source"


# --- SQLAlchemy Database Model ---

class OpportunityModel(Base):
    __tablename__ = "opportunities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    organisation: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    location: Mapped[str] = mapped_column(String(150), default="Remote")
    eligibility: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    deadline: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    application_url: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str] = mapped_column(String(50), default=OpportunityCategoryEnum.INTERNSHIP.value, index=True)
    date_discovered: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


# --- Pydantic Schemas ---

class OpportunityCreate(BaseModel):
    title: str = Field(..., description="Opportunity name (e.g. Data Science Internship)")
    organisation: str = Field(..., description="Hosting company or institution")
    location: Optional[str] = Field("Remote", description="Job location or remote status")
    eligibility: Optional[str] = Field(None, description="Target applicant requirements")
    deadline: Optional[str] = Field(None, description="Application deadline date")
    application_url: str = Field(..., description="Direct link to apply")
    category: OpportunityCategoryEnum = Field(OpportunityCategoryEnum.INTERNSHIP, description="Opportunity category")


class OpportunityResponse(BaseModel):
    id: str
    title: str
    organisation: str
    location: str
    eligibility: Optional[str] = None
    deadline: Optional[str] = None
    application_url: str
    category: OpportunityCategoryEnum
    date_discovered: datetime.datetime