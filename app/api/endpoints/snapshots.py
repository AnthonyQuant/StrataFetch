from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.snapshot import (
    ScrapeSessionCreate,
    ScrapeSessionResponse,
)
from app.services.snapshot_service import SnapshotService

router = APIRouter(prefix="/api/snapshots", tags=["Historical Snapshot & Storage Engine"])


@router.post("/save", response_model=ScrapeSessionResponse)
async def save_snapshot_session(
    payload: ScrapeSessionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Stores a complete scraping run as a historical snapshot session with record hashes."""
    session_model = await SnapshotService.create_snapshot_session(db, payload)
    return session_model


@router.get("/list", response_model=List[ScrapeSessionResponse])
async def list_snapshot_sessions(
    profile_name: Optional[str] = Query(None, description="Filter snapshots by extraction profile name"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Lists saved historical scraping sessions."""
    return await SnapshotService.list_sessions(db, profile_name=profile_name, limit=limit)


@router.get("/{session_id}", response_model=Dict[str, Any])
async def get_snapshot_session_details(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves full session metadata and associated record snapshots."""
    session_model = await SnapshotService.get_session_by_id(db, session_id)
    if not session_model:
        raise HTTPException(status_code=404, detail="Snapshot session not found")

    return {
        "id": session_model.id,
        "profile_name": session_model.profile_name,
        "target_url": session_model.target_url,
        "created_at": session_model.created_at,
        "total_records": session_model.total_records,
        "session_hash": session_model.session_hash,
        "records": [
            {
                "id": r.id,
                "record_index": r.record_index,
                "raw_data": r.raw_data,
                "normalized_data": r.normalized_data,
                "record_hash": r.record_hash,
                "created_at": r.created_at
            }
            for r in session_model.records
        ]
    }