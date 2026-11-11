from typing import Any, Dict, Optional
import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from app.services.selector_generator import SelectorGeneratorService

router = APIRouter(prefix="/api/selector", tags=["Visual Selector Builder"])


class ProxyFetchRequest(BaseModel):
    url: str = Field(..., description="Target webpage URL to inspect in visual builder")


class SelectorAnalyzeRequest(BaseModel):
    html_content: str = Field(..., description="Raw HTML string of the target page")
    selected_text: str = Field(..., description="Text content selected by user to generate CSS selector")


@router.post("/proxy-fetch", response_class=HTMLResponse)
async def proxy_fetch_url(payload: ProxyFetchRequest):
    """Fetches target page HTML for rendering inside the selector builder workspace."""
    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = await client.get(payload.url, headers=headers)
            response.raise_for_status()
            return HTMLResponse(content=response.text, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch proxy URL: {str(e)}")


@router.post("/analyze", response_model=Dict[str, Any])
async def analyze_selector(payload: SelectorAnalyzeRequest):
    """Generates suggested CSS selectors based on user selected element text."""
    return SelectorGeneratorService.analyze_element_selection(
        payload.html_content, payload.selected_text
    )