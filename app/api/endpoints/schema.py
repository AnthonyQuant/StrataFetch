from typing import Any, Dict, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field, HttpUrl
from app.services.http_client import HTTPClientService
from app.services.schema_detector import SchemaDetectorService

router = APIRouter(prefix="/api/schema", tags=["Automatic Schema Detection Engine"])


class AutoDetectSchemaRequest(BaseModel):
    url: Optional[HttpUrl] = Field(None, description="Target URL to fetch and auto-detect schema from")
    html_content: Optional[str] = Field(None, description="Raw HTML string if already fetched")
    container_selector: Optional[str] = Field(None, description="Optional CSS wrapper class to isolate container")


@router.post("/detect", response_model=Dict[str, Any])
async def detect_schema_from_page(payload: AutoDetectSchemaRequest):
    """Analyzes raw HTML or fetches target URL to automatically suggest repeating wrapper classes and field extraction rules."""
    html_to_analyze = payload.html_content

    if not html_to_analyze and payload.url:
        fetch_res = await HTTPClientService.fetch_page(str(payload.url))
        if not fetch_res["success"]:
            return {
                "error": f"Failed to fetch target URL for schema detection: {fetch_res['error']}",
                "suggested_rules": []
            }
        html_to_analyze = fetch_res["html_content"]

    if not html_to_analyze:
        return {
            "error": "Either 'url' or 'html_content' must be provided.",
            "suggested_rules": []
        }

    return SchemaDetectorService.auto_detect_schema(
        html_content=html_to_analyze,
        container_selector=payload.container_selector
    )