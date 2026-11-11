from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.health_monitor import ProfileHealthReport, SelectorHealthService
from app.services.snapshot_service import SnapshotService

router = APIRouter(prefix="/api/health-monitor", tags=["Selector Health & Drift Detection Engine"])


class EvaluateHealthRequest(BaseModel):
    profile_name: str = Field(..., description="Name of extraction profile")
    records_extracted: int = Field(..., ge=0, description="Records extracted in current run")
    records_expected: int = Field(..., ge=1, description="Historical baseline expected record count")
    previous_success_rate: float = Field(98.2, ge=0.0, le=100.0)


@router.post("/evaluate", response_model=ProfileHealthReport)
async def evaluate_health_endpoint(payload: EvaluateHealthRequest):
    """Evaluates extraction yield against baseline expectations to detect structural DOM drift."""
    return SelectorHealthService.evaluate_profile_health(
        profile_name=payload.profile_name,
        current_extracted_count=payload.records_extracted,
        historical_expected_count=payload.records_expected,
        previous_success_rate=payload.previous_success_rate
    )


@router.get("/profile/{profile_name}", response_model=ProfileHealthReport)
async def get_profile_health_from_db(
    profile_name: str,
    db: AsyncSession = Depends(get_db)
):
    """Computes health status for a profile by comparing its 2 most recent stored snapshot runs."""
    sessions = await SnapshotService.get_latest_two_sessions(db, profile_name)
    if len(sessions) < 2:
        return ProfileHealthReport(
            profile_name=profile_name,
            status="Healthy",
            current_success_rate=100.0,
            previous_success_rate=100.0,
            records_expected=sessions[0].total_records if sessions else 0,
            records_extracted=sessions[0].total_records if sessions else 0,
            yield_drop_percentage=0.0,
            warning_message="Insufficient run history (requires 2+ snapshot sessions for automated drift audit)."
        )

    curr_session, prev_session = sessions[0], sessions[1]
    expected_count = prev_session.total_records
    current_count = curr_session.total_records

    return SelectorHealthService.evaluate_profile_health(
        profile_name=profile_name,
        current_extracted_count=current_count,
        historical_expected_count=expected_count
    )