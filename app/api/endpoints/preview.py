from typing import Any, Dict, List, Optional
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.models.extraction_profile import FieldExtractionRule
from app.services.html_extractor import HTMLExtractorService

router = APIRouter(prefix="/api/preview", tags=["Preview Engine"])


class HTMLPreviewRequest(BaseModel):
    html_content: Optional[str] = Field(None, description="Raw HTML string to parse")
    url: Optional[str] = Field(None, description="Target URL to fetch HTML from")
    rules: Optional[List[FieldExtractionRule]] = Field(default=[], description="Extraction rules to evaluate")


@router.post("/extract", response_model=Dict[str, Any])
async def preview_extraction(payload: HTMLPreviewRequest):
    html_content = payload.html_content

    if not html_content and payload.url:
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                response = await client.get(payload.url, headers={"User-Agent": "StrataFetch/1.0"})
                response.raise_for_status()
                html_content = response.text
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to fetch HTML from URL: {str(e)}")

    if not html_content:
        raise HTTPException(status_code=400, detail="Either 'html_content' or a valid 'url' must be provided.")

    return HTMLExtractorService.process_html_preview(html_content, payload.rules)