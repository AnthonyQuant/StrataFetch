from typing import Any, Dict, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field, HttpUrl
from app.services.http_client import HTTPClientService
from app.services.metadata_extractor import MetadataExtractorService

router = APIRouter(prefix="/api/metadata", tags=["Structured Metadata Extractor"])


class MetadataExtractRequest(BaseModel):
    url: Optional[HttpUrl] = Field(None, description="Target webpage URL to fetch and extract metadata from")
    html_content: Optional[str] = Field(None, description="Raw HTML string if already fetched")


@router.post("/extract", response_model=Dict[str, Any])
async def extract_structured_metadata(payload: MetadataExtractRequest):
    """Extracts JSON-LD schemas, Open Graph properties, and Twitter Card tags from raw HTML or URL."""
    html_to_analyze = payload.html_content

    if not html_to_analyze and payload.url:
        fetch_res = await HTTPClientService.fetch_page(str(payload.url))
        if not fetch_res["success"]:
            return {
                "error": f"Failed to fetch target URL for metadata extraction: {fetch_res['error']}",
                "has_structured_metadata": False
            }
        html_to_analyze = fetch_res["html_content"]

    if not html_to_analyze:
        return {
            "error": "Either 'url' or 'html_content' must be provided.",
            "has_structured_metadata": False
        }

    return MetadataExtractorService.extract_all_metadata(html_to_analyze)