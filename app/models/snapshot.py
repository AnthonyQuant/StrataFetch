import datetime
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy import DateTime, ForeignKey, Integer, String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


# --- SQLAlchemy Database Models ---

class ScrapeSessionModel(Base):
    __tablename__ = "scrape_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    target_url: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    total_records: Mapped[int] = mapped_column(Integer, default=0)
    session_hash: Mapped[str] = mapped_column(String(64), nullable=True)

    records: Mapped[List["RecordSnapshotModel"]] = relationship(
        "RecordSnapshotModel", back_populates="session", cascade="all, delete-orphan"
    )


class RecordSnapshotModel(Base):
    __tablename__ = "record_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("scrape_sessions.id", ondelete="CASCADE"), nullable=False)
    record_index: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    normalized_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    record_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    session: Mapped["ScrapeSessionModel"] = relationship("ScrapeSessionModel", back_populates="records")


# --- Pydantic Schemas for API Serialization ---

class RecordSnapshotCreate(BaseModel):
    record_index: int = Field(..., description="Sequential position index of extracted item")
    raw_data: Dict[str, Any] = Field(..., description="Original raw extraction dictionary")
    normalized_data: Dict[str, Any] = Field(..., description="Cleaned/normalized data dictionary")


class ScrapeSessionCreate(BaseModel):
    profile_name: str = Field(..., description="Name of the extraction profile executed")
    target_url: str = Field(..., description="Target webpage URL scraped")
    records: List[RecordSnapshotCreate] = Field(..., description="List of extracted records")


class ScrapeSessionResponse(BaseModel):
    id: str
    profile_name: str
    target_url: str
    created_at: datetime.datetime
    total_records: int
    session_hash: Optional[str] = None