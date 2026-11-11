from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.execution_log import ExecutionLogModel, ExecutionLogCreate


class ExecutionLoggerService:
    """Manages audit logging and request-level telemetry recording."""

    @classmethod
    async def log_execution(
        cls,
        db: AsyncSession,
        payload: ExecutionLogCreate
    ) -> ExecutionLogModel:
        log_entry = ExecutionLogModel(
            job_id=payload.job_id,
            target_url=payload.target_url,
            status_code=payload.status_code,
            response_time_ms=payload.response_time_ms,
            success=payload.success,
            error_message=payload.error_message,
            log_level=payload.log_level or ("ERROR" if not payload.success else "INFO")
        )
        db.add(log_entry)
        await db.commit()
        await db.refresh(log_entry)
        return log_entry

    @staticmethod
    async def list_logs(
        db: AsyncSession,
        job_id: Optional[str] = None,
        only_failures: bool = False,
        limit: int = 50
    ) -> List[ExecutionLogModel]:
        stmt = select(ExecutionLogModel).order_by(desc(ExecutionLogModel.created_at)).limit(limit)

        if job_id:
            stmt = stmt.where(ExecutionLogModel.job_id == job_id)
        if only_failures:
            stmt = stmt.where(ExecutionLogModel.success == False)

        res = await db.execute(stmt)
        return list(res.scalars().all())