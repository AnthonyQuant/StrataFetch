from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.diff_engine import DiffEngineService, SessionDiffReport
from app.services.snapshot_service import SnapshotService

router = APIRouter(prefix="/api/changes", tags=["Change Detection & Historical Tracking Engine"])


class CompareSessionsRequest(BaseModel):
    previous_session_id: str = Field(..., description="UUID of older snapshot session")
    current_session_id: str = Field(..., description="UUID of newer snapshot session")
    primary_key_field: Optional[str] = Field(None, description="Field name used to align matching items across runs (e.g. 'product_name', 'url')")


@router.post("/compare-sessions", response_model=SessionDiffReport)
async def compare_sessions_endpoint(
    payload: CompareSessionsRequest,
    db: AsyncSession = Depends(get_db)
):
    """Compares two specific historical snapshot sessions to compute delta tracking reports."""
    prev_session = await SnapshotService.get_session_by_id(db, payload.previous_session_id)
    if not prev_session:
        raise HTTPException(status_code=404, detail=f"Previous session {payload.previous_session_id} not found")

    curr_session = await SnapshotService.get_session_by_id(db, payload.current_session_id)
    if not curr_session:
        raise HTTPException(status_code=404, detail=f"Current session {payload.current_session_id} not found")

    prev_records = [r.normalized_data for r in prev_session.records]
    curr_records = [r.normalized_data for r in curr_session.records]

    return DiffEngineService.compare_sessions(
        previous_session_id=prev_session.id,
        current_session_id=curr_session.id,
        profile_name=curr_session.profile_name,
        previous_records=prev_records,
        current_records=curr_records,
        primary_key_field=payload.primary_key_field
    )


@router.get("/latest-delta/{profile_name}", response_model=SessionDiffReport)
async def get_latest_profile_delta(
    profile_name: str,
    primary_key_field: Optional[str] = Query(None, description="Primary key field to align matching records"),
    db: AsyncSession = Depends(get_db)
):
    """Automatically fetches the 2 most recent runs for a profile and returns delta diff analysis."""
    latest_two = await SnapshotService.get_latest_two_sessions(db, profile_name)
    if len(latest_two) < 2:
        raise HTTPException(
            status_code=400,
            detail=f"At least 2 snapshot sessions are required to calculate delta tracking for profile '{profile_name}'. Found {len(latest_two)}."
        )

    curr_session, prev_session = latest_two[0], latest_two[1]

    prev_records = [r.normalized_data for r in prev_session.records]
    curr_records = [r.normalized_data for r in curr_session.records]

    return DiffEngineService.compare_sessions(
        previous_session_id=prev_session.id,
        current_session_id=curr_session.id,
        profile_name=profile_name,
        previous_records=prev_records,
        current_records=curr_records,
        primary_key_field=primary_key_field
    )