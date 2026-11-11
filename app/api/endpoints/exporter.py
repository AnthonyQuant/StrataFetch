from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, Response, HTTPException
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.opportunity import OpportunityModel
from app.services.exporter_service import DataExporterService
from app.services.webhook_service import WebhookDispatchService

router = APIRouter(prefix="/api/export", tags=["Data Export & Webhook Integration Engine"])


class ExportRequest(BaseModel):
    records: List[Dict[str, Any]] = Field(..., description="Array of extracted dictionary records to format")
    format: str = Field("csv", description="Output format: 'csv', 'json', or 'jsonl'")


class WebhookTestRequest(BaseModel):
    webhook_url: HttpUrl = Field(..., description="Target webhook URL to receive payload")
    event_type: str = Field("crawl_completed", description="Event topic name")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Custom dataset or alert body")


@router.post("/download")
async def export_records_direct(payload: ExportRequest):
    """Converts a raw JSON records array into downloadable CSV, JSON, or JSONL files."""
    fmt = payload.format.lower()

    if fmt == "csv":
        content = DataExporterService.to_csv(payload.records)
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=extracted_data.csv"}
        )
    elif fmt == "jsonl":
        content = DataExporterService.to_jsonl(payload.records)
        return Response(
            content=content,
            media_type="application/x-ndjson",
            headers={"Content-Disposition": "attachment; filename=extracted_data.jsonl"}
        )
    elif fmt == "json":
        content = DataExporterService.to_json(payload.records)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=extracted_data.json"}
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported format. Supported options: 'csv', 'json', 'jsonl'.")


@router.get("/opportunities")
async def export_opportunities(
    format: str = Query("csv", description="Export format: 'csv', 'json', 'jsonl'"),
    category: Optional[str] = Query(None, description="Optional category filter"),
    db: AsyncSession = Depends(get_db)
):
    """Exports ingested opportunities directly from database into desired file format."""
    stmt = select(OpportunityModel)
    if category:
        stmt = stmt.where(OpportunityModel.category == category)

    res = await db.execute(stmt)
    records = res.scalars().all()

    data_dicts = [
        {
            "id": r.id,
            "title": r.title,
            "organisation": r.organisation,
            "location": r.location,
            "eligibility": r.eligibility,
            "deadline": r.deadline,
            "application_url": r.application_url,
            "category": r.category,
            "date_discovered": r.date_discovered.isoformat()
        }
        for r in records
    ]

    fmt = format.lower()
    if fmt == "csv":
        content = DataExporterService.to_csv(data_dicts)
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=opportunities_{category or 'all'}.csv"}
        )
    elif fmt == "jsonl":
        content = DataExporterService.to_jsonl(data_dicts)
        return Response(
            content=content,
            media_type="application/x-ndjson",
            headers={"Content-Disposition": f"attachment; filename=opportunities_{category or 'all'}.jsonl"}
        )
    else:
        content = DataExporterService.to_json(data_dicts)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=opportunities_{category or 'all'}.json"}
        )


@router.post("/webhook/dispatch")
async def dispatch_webhook_test(payload: WebhookTestRequest):
    """Dispatches a test notification payload to an external webhook endpoint."""
    event_payload = {
        "event": payload.event_type,
        "data": payload.payload
    }
    return await WebhookDispatchService.send_webhook(str(payload.webhook_url), event_payload)