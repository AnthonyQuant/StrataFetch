import hashlib
import json
from typing import Any, Dict, List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.snapshot import (
    ScrapeSessionModel,
    RecordSnapshotModel,
    ScrapeSessionCreate,
)


class SnapshotService:
    """Manages creation, hashing, and retrieval of historical extraction snapshots."""

    @staticmethod
    def compute_record_hash(normalized_data: Dict[str, Any]) -> str:
        """Computes a deterministic MD5 hash of a normalized record dictionary."""
        sorted_items = sorted((str(k), str(v)) for k, v in normalized_data.items())
        serialized = json.dumps(sorted_items, sort_keys=True)
        return hashlib.md5(serialized.encode("utf-8")).hexdigest()

    @classmethod
    def compute_session_hash(cls, record_hashes: List[str]) -> str:
        """Computes an overall session hash from an ordered list of record hashes."""
        combined = ":".join(sorted(record_hashes))
        return hashlib.md5(combined.encode("utf-8")).hexdigest()

    @classmethod
    async def create_snapshot_session(
        cls,
        db: AsyncSession,
        payload: ScrapeSessionCreate
    ) -> ScrapeSessionModel:
        record_hashes: List[str] = []
        record_models: List[RecordSnapshotModel] = []

        for item in payload.records:
            rec_hash = cls.compute_record_hash(item.normalized_data)
            record_hashes.append(rec_hash)

            rec_model = RecordSnapshotModel(
                record_index=item.record_index,
                raw_data=item.raw_data,
                normalized_data=item.normalized_data,
                record_hash=rec_hash
            )
            record_models.append(rec_model)

        session_hash = cls.compute_session_hash(record_hashes)

        session_model = ScrapeSessionModel(
            profile_name=payload.profile_name,
            target_url=payload.target_url,
            total_records=len(payload.records),
            session_hash=session_hash,
            records=record_models
        )

        db.add(session_model)
        await db.commit()
        await db.refresh(session_model)
        return session_model

    @staticmethod
    async def get_session_by_id(
        db: AsyncSession,
        session_id: str
    ) -> Optional[ScrapeSessionModel]:
        stmt = (
            select(ScrapeSessionModel)
            .options(selectinload(ScrapeSessionModel.records))
            .where(ScrapeSessionModel.id == session_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_sessions(
        db: AsyncSession,
        profile_name: Optional[str] = None,
        limit: int = 20
    ) -> List[ScrapeSessionModel]:
        stmt = select(ScrapeSessionModel).order_by(desc(ScrapeSessionModel.created_at)).limit(limit)
        if profile_name:
            stmt = stmt.where(ScrapeSessionModel.profile_name == profile_name)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_latest_two_sessions(
        db: AsyncSession,
        profile_name: str
    ) -> List[ScrapeSessionModel]:
        stmt = (
            select(ScrapeSessionModel)
            .options(selectinload(ScrapeSessionModel.records))
            .where(ScrapeSessionModel.profile_name == profile_name)
            .order_by(desc(ScrapeSessionModel.created_at))
            .limit(2)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())