from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.opportunity import OpportunityCreate, OpportunityResponse, OpportunityCategoryEnum
from app.services.opportunity_service import OpportunityService

router = APIRouter(prefix="/api/opportunities", tags=["Opportunity & Grant Scraper Engine"])


class RawIngestRequest(BaseModel):
    records: List[Dict[str, Any]] = Field(..., description="Raw extracted dict records array")
    category: OpportunityCategoryEnum = Field(OpportunityCategoryEnum.INTERNSHIP, description="Category classification")


@router.post("/ingest", response_model=List[OpportunityResponse])
async def ingest_raw_extracted_opportunities(
    payload: RawIngestRequest,
    db: AsyncSession = Depends(get_db)
):
    """Normalizes and saves raw extracted web records as standardized Opportunity entities."""
    return await OpportunityService.ingest_raw_records(db, payload.records, default_category=payload.category)


@router.post("/create", response_model=OpportunityResponse)
async def create_single_opportunity(
    payload: OpportunityCreate,
    db: AsyncSession = Depends(get_db)
):
    """Creates a standardized opportunity entry directly."""
    return await OpportunityService.create_opportunity(db, payload)


@router.get("/list", response_model=List[OpportunityResponse])
async def list_opportunities(
    category: Optional[OpportunityCategoryEnum] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search term for title, organisation, or eligibility"),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Lists and searches ingested opportunities."""
    return await OpportunityService.list_opportunities(db, category=category, search_query=search, limit=limit)