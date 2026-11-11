import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class JobStatusEnum(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobTypeEnum(str, Enum):
    ONE_OFF = "one_off"
    INTERVAL = "interval"


class JobCreateRequest(BaseModel):
    profile_name: str = Field(..., description="Target extraction profile name")
    seed_url: str = Field(..., description="Starting target URL for the job")
    max_depth: int = Field(2, ge=1, le=5, description="Maximum crawling depth")
    max_pages: int = Field(10, ge=1, le=100, description="Maximum pages to extract")
    interval_seconds: Optional[int] = Field(None, ge=10, description="Interval in seconds for recurring execution (e.g. 300 for 5 mins)")


class JobResponse(BaseModel):
    job_id: str
    profile_name: str
    seed_url: str
    job_type: JobTypeEnum
    status: JobStatusEnum
    created_at: str
    last_run_at: Optional[str] = None
    next_run_at: Optional[str] = None
    run_count: int = 0
    interval_seconds: Optional[int] = None
    last_result_summary: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None