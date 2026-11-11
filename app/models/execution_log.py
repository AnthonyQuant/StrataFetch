import datetime
import uuid
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


# --- SQLAlchemy Database Model ---

class ExecutionLogModel(Base):
    __tablename__ = "execution_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    target_url: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    response_time_ms: Mapped[float] = mapped_column(Float, nullable=False)
    success: Mapped[bool] = mapped_column(nullable=False, index=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    log_level: Mapped[str] = mapped_column(String(20), default="INFO", index=True)  # INFO, WARNING, ERROR
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


# --- Pydantic Schemas ---

class ExecutionLogCreate(BaseModel):
    job_id: Optional[str] = Field(None, description="Associated job run UUID")
    target_url: str = Field(..., description="Target webpage URL fetched")
    status_code: int = Field(..., description="HTTP status code returned")
    response_time_ms: float = Field(..., description="Fetch latency in milliseconds")
    success: bool = Field(..., description="Whether fetch succeeded")
    error_message: Optional[str] = Field(None, description="Error message or stack trace if failed")
    log_level: Optional[str] = Field("INFO", description="Log level: INFO, WARNING, ERROR")


class ExecutionLogResponse(BaseModel):
    id: str
    job_id: Optional[str] = None
    target_url: str
    status_code: int
    response_time_ms: float
    success: bool
    error_message: Optional[str] = None
    log_level: str
    created_at: datetime.datetime