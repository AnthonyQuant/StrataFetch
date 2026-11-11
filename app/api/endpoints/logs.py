from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.execution_log import ExecutionLogCreate, ExecutionLogResponse
from app.services.logger_service import ExecutionLoggerService

router = APIRouter(prefix="/api/logs", tags=["Granular Execution Logging & Audit System"])


@router.post("/record", response_model=ExecutionLogResponse)
async def record_execution_log(
    payload: ExecutionLogCreate,
    db: AsyncSession = Depends(get_db)
):
    """Records an execution telemetry log entry."""
    return await ExecutionLoggerService.log_execution(db, payload)


@router.get("/list", response_model=List[ExecutionLogResponse])
async def list_execution_logs(
    job_id: Optional[str] = Query(None, description="Filter logs by job ID"),
    only_failures: bool = Query(False, description="Filter strictly failed HTTP requests/errors"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves execution audit logs and failure traces."""
    return await ExecutionLoggerService.list_logs(db, job_id=job_id, only_failures=only_failures, limit=limit)