import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import select, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.opportunity import OpportunityModel, OpportunityCreate, OpportunityCategoryEnum


class OpportunityService:
    """Manages ingestion and queries for standardized student and career opportunities."""

    @classmethod
    async def create_opportunity(
        cls,
        db: AsyncSession,
        payload: OpportunityCreate
    ) -> OpportunityModel:
        opp = OpportunityModel(
            title=payload.title,
            organisation=payload.organisation,
            location=payload.location or "Remote",
            eligibility=payload.eligibility,
            deadline=payload.deadline,
            application_url=payload.application_url,
            category=payload.category.value
        )
        db.add(opp)
        await db.commit()
        await db.refresh(opp)
        return opp

    @classmethod
    async def ingest_raw_records(
        cls,
        db: AsyncSession,
        records: List[Dict[str, Any]],
        default_category: OpportunityCategoryEnum = OpportunityCategoryEnum.INTERNSHIP
    ) -> List[OpportunityModel]:
        """Maps raw extracted record dicts to standardized Opportunity entities."""
        saved_entities: List[OpportunityModel] = []

        for r in records:
            title = r.get("opportunity") or r.get("title") or r.get("name") or "Untitled Opportunity"
            org = r.get("organisation") or r.get("organization") or r.get("company") or "Unknown Organisation"
            loc = r.get("location") or "Remote"
            elig = r.get("eligibility") or r.get("requirements")
            dl = r.get("deadline") or r.get("due_date")
            app_url = r.get("application_url") or r.get("url") or r.get("link") or "#"

            opp = OpportunityModel(
                title=str(title),
                organisation=str(org),
                location=str(loc),
                eligibility=str(elig) if elig else None,
                deadline=str(dl) if dl else None,
                application_url=str(app_url),
                category=default_category.value
            )
            db.add(opp)
            saved_entities.append(opp)

        await db.commit()
        for item in saved_entities:
            await db.refresh(item)

        return saved_entities

    @classmethod
    async def list_opportunities(
        cls,
        db: AsyncSession,
        category: Optional[OpportunityCategoryEnum] = None,
        search_query: Optional[str] = None,
        limit: int = 50
    ) -> List[OpportunityModel]:
        stmt = select(OpportunityModel).order_by(desc(OpportunityModel.date_discovered)).limit(limit)

        if category:
            stmt = stmt.where(OpportunityModel.category == category.value)

        if search_query:
            term = f"%{search_query}%"
            stmt = stmt.where(
                or_(
                    OpportunityModel.title.ilike(term),
                    OpportunityModel.organisation.ilike(term),
                    OpportunityModel.eligibility.ilike(term)
                )
            )

        res = await db.execute(stmt)
        return list(res.scalars().all())