import datetime
import uuid
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


# --- SQLAlchemy Database Model ---

class HTMLSnapshotModel(Base):
    __tablename__ = "html_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    target_url: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    html_content: Mapped[str] = mapped_column(Text, nullable=False)
    content_length: Mapped[int] = mapped_column(Integer, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


# --- Pydantic Schemas ---

class HTMLSnapshotCreate(BaseModel):
    target_url: str = Field(..., description="Target webpage URL")
    html_content: str = Field(..., description="Raw HTML string content to archive")


class HTMLSnapshotResponse(BaseModel):
    id: str
    target_url: str
    content_length: int
    content_hash: str
    created_at: datetime.datetime