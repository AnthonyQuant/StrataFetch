import asyncio
import datetime
import uuid
from typing import Any, Dict, List, Optional

from app.models.job import JobCreateRequest, JobResponse, JobStatusEnum, JobTypeEnum
from app.services.crawler import DeepCrawlerService


class JobSchedulerService:
    """In-memory asyncio background job runner and recurring task scheduler."""

    def __init__(self):
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.active_tasks: Dict[str, asyncio.Task] = {}

    def create_job(self, payload: JobCreateRequest) -> JobResponse:
        job_id = str(uuid.uuid4())
        now_str = datetime.datetime.utcnow().isoformat()
        job_type = JobTypeEnum.INTERVAL if payload.interval_seconds else JobTypeEnum.ONE_OFF

        job_data = {
            "job_id": job_id,
            "profile_name": payload.profile_name,
            "seed_url": payload.seed_url,
            "max_depth": payload.max_depth,
            "max_pages": payload.max_pages,
            "job_type": job_type,
            "status": JobStatusEnum.PENDING,
            "created_at": now_str,
            "last_run_at": None,
            "next_run_at": now_str if job_type == JobTypeEnum.ONE_OFF else now_str,
            "run_count": 0,
            "interval_seconds": payload.interval_seconds,
            "last_result_summary": None,
            "error_message": None,
        }

        self.jobs[job_id] = job_data

        if job_type == JobTypeEnum.ONE_OFF:
            task = asyncio.create_task(self._run_one_off_job(job_id))
            self.active_tasks[job_id] = task
        else:
            task = asyncio.create_task(self._run_interval_job(job_id))
            self.active_tasks[job_id] = task

        return JobResponse(**job_data)

    async def _execute_crawl_task(self, job_id: str) -> Dict[str, Any]:
        job = self.jobs[job_id]
        crawler = DeepCrawlerService(
            seed_url=job["seed_url"],
            max_depth=job["max_depth"],
            max_pages=job["max_pages"],
            restrict_domain=True,
            force_playwright=False,
            concurrency=5
        )
        return await crawler.run_crawl()

    async def _run_one_off_job(self, job_id: str):
        if job_id not in self.jobs:
            return
        job = self.jobs[job_id]
        job["status"] = JobStatusEnum.RUNNING
        job["last_run_at"] = datetime.datetime.utcnow().isoformat()

        try:
            result = await self._execute_crawl_task(job_id)
            job["status"] = JobStatusEnum.COMPLETED
            job["run_count"] += 1
            job["last_result_summary"] = {
                "total_crawled": result.get("total_crawled", 0),
                "total_discovered": result.get("total_discovered", 0)
            }
        except asyncio.CancelledError:
            job["status"] = JobStatusEnum.CANCELLED
        except Exception as e:
            job["status"] = JobStatusEnum.FAILED
            job["error_message"] = str(e)
        finally:
            self.active_tasks.pop(job_id, None)

    async def _run_interval_job(self, job_id: str):
        if job_id not in self.jobs:
            return
        job = self.jobs[job_id]
        interval = job["interval_seconds"] or 60

        try:
            while True:
                job["status"] = JobStatusEnum.RUNNING
                job["last_run_at"] = datetime.datetime.utcnow().isoformat()

                try:
                    result = await self._execute_crawl_task(job_id)
                    job["status"] = JobStatusEnum.PENDING
                    job["run_count"] += 1
                    job["last_result_summary"] = {
                        "total_crawled": result.get("total_crawled", 0),
                        "total_discovered": result.get("total_discovered", 0)
                    }
                except Exception as e:
                    job["status"] = JobStatusEnum.FAILED
                    job["error_message"] = str(e)

                next_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=interval)
                job["next_run_at"] = next_time.isoformat()
                await asyncio.sleep(interval)

        except asyncio.CancelledError:
            job["status"] = JobStatusEnum.CANCELLED
            job["next_run_at"] = None
        finally:
            self.active_tasks.pop(job_id, None)

    def cancel_job(self, job_id: str) -> bool:
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = JobStatusEnum.CANCELLED
            self.jobs[job_id]["next_run_at"] = None
            if job_id in self.active_tasks:
                self.active_tasks[job_id].cancel()
                self.active_tasks.pop(job_id, None)
            return True
        return False

    def get_job(self, job_id: str) -> Optional[JobResponse]:
        data = self.jobs.get(job_id)
        return JobResponse(**data) if data else None

    def list_jobs(self) -> List[JobResponse]:
        return [JobResponse(**data) for data in self.jobs.values()]


# Global Singleton Scheduler Instance
job_scheduler_service = JobSchedulerService()