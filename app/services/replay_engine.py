import hashlib
from typing import Any, Dict, List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.extraction_profile import ExtractionProfile
from app.models.html_snapshot import HTMLSnapshotModel, HTMLSnapshotCreate
from app.services.html_extractor import HTMLExtractorService

class ReplayEngineService:
    """Manages raw HTML DOM snapshot archiving and offline extraction rule replays."""

    @staticmethod
    def compute_html_hash(html_content: str) -> str:
        return hashlib.md5(html_content.encode("utf-8")).hexdigest()

    @classmethod
    async def save_html_snapshot(
        cls,
        db: AsyncSession,
        payload: HTMLSnapshotCreate
    ) -> HTMLSnapshotModel:
        content_hash = cls.compute_html_hash(payload.html_content)

        snapshot = HTMLSnapshotModel(
            target_url=payload.target_url,
            html_content=payload.html_content,
            content_length=len(payload.html_content),
            content_hash=content_hash
        )

        db.add(snapshot)
        await db.commit()
        await db.refresh(snapshot)
        return snapshot

    @staticmethod
    async def get_snapshot_by_id(db: AsyncSession, snapshot_id: str) -> Optional[HTMLSnapshotModel]:
        stmt = select(HTMLSnapshotModel).where(HTMLSnapshotModel.id == snapshot_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def list_snapshots(db: AsyncSession, limit: int = 20) -> List[HTMLSnapshotModel]:
        stmt = select(HTMLSnapshotModel).order_by(desc(HTMLSnapshotModel.created_at)).limit(limit)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @classmethod
    async def replay_extraction_on_snapshot(
        cls,
        db: AsyncSession,
        snapshot_id: str,
        profile: ExtractionProfile
    ) -> Dict[str, Any]:
        """Re-runs rule extractions offline against an archived raw HTML snapshot without making network calls."""
        snapshot = await cls.get_snapshot_by_id(db, snapshot_id)
        if not snapshot:
            return {"error": f"HTML Snapshot '{snapshot_id}' not found.", "success": False}

        extracted_records = HTMLExtractorService.extract(
            html_content=snapshot.html_content,
            container_selector=profile.container_selector,
            rules=profile.field_rules
        )

        return {
            "snapshot_id": snapshot.id,
            "target_url": snapshot.target_url,
            "archived_at": snapshot.created_at.isoformat(),
            "profile_name": profile.name,
            "total_records_extracted": len(extracted_records),
            "records": extracted_records,
            "success": True
        }