from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.extraction_profile import ExtractionProfile
from app.models.html_snapshot import HTMLSnapshotCreate, HTMLSnapshotResponse
from app.services.replay_engine import ReplayEngineService

router = APIRouter(prefix="/api/replay", tags=["Offline Crawl Replay & HTML Snapshot Engine"])


class ReplayRequest(BaseModel):
    snapshot_id: str = Field(..., description="UUID of archived raw HTML snapshot")
    profile: ExtractionProfile = Field(..., description="Extraction rules profile to re-evaluate offline")


@router.post("/archive", response_model=HTMLSnapshotResponse)
async def archive_html_snapshot(
    payload: HTMLSnapshotCreate,
    db: AsyncSession = Depends(get_db)
):
    """Archives a raw HTML payload to storage for offline inspection and replay."""
    return await ReplayEngineService.save_html_snapshot(db, payload)


@router.get("/snapshots", response_model=List[HTMLSnapshotResponse])
async def list_html_snapshots(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Lists saved raw HTML snapshots available for offline replay."""
    return await ReplayEngineService.list_snapshots(db, limit=limit)


@router.post("/run", response_model=Dict[str, Any])
async def replay_extraction_offline(
    payload: ReplayRequest,
    db: AsyncSession = Depends(get_db)
):
    """Executes rule extractions against an archived HTML snapshot without making network requests."""
    result = await ReplayEngineService.replay_extraction_on_snapshot(db, payload.snapshot_id, payload.profile)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result