from typing import List
from fastapi import APIRouter, HTTPException

from app.models.job import JobCreateRequest, JobResponse
from app.services.job_scheduler import job_scheduler_service

router = APIRouter(prefix="/api/jobs", tags=["Background Job Scheduler Engine"])


@router.post("/trigger", response_model=JobResponse)
async def trigger_one_off_job(payload: JobCreateRequest):
    """Triggers an immediate background crawling job."""
    payload.interval_seconds = None
    return job_scheduler_service.create_job(payload)


@router.post("/schedule", response_model=JobResponse)
async def schedule_recurring_job(payload: JobCreateRequest):
    """Schedules a recurring background crawling job with a repeating interval."""
    if not payload.interval_seconds:
        raise HTTPException(status_code=400, detail="field 'interval_seconds' is required for recurring scheduled jobs.")
    return job_scheduler_service.create_job(payload)


@router.get("/list", response_model=List[JobResponse])
async def list_jobs():
    """Lists all active, pending, and completed background jobs."""
    return job_scheduler_service.list_jobs()


@router.get("/{job_id}", response_model=JobResponse)
async def get_job_details(job_id: str):
    """Retrieves status and runtime metrics for a specific job."""
    job = job_scheduler_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/{job_id}/cancel", response_model=JobResponse)
async def cancel_job(job_id: str):
    """Cancels an active or scheduled background job."""
    success = job_scheduler_service.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_scheduler_service.get_job(job_id)