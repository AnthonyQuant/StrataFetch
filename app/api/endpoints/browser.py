from typing import Any, Dict, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field, HttpUrl
from app.services.browser_service import DynamicBrowserService

router = APIRouter(prefix="/api/browser", tags=["Dynamic JavaScript Browser Renderer Engine"])


class DynamicRenderRequest(BaseModel):
    url: HttpUrl = Field(..., description="Target web page URL to render dynamically")
    wait_for_selector: Optional[str] = Field(None, description="CSS selector to wait for before extracting DOM HTML")
    timeout_seconds: int = Field(30, ge=5, le=120, description="Max page render timeout in seconds")
    scroll_to_bottom: bool = Field(False, description="Trigger scrolling down to force lazy-loaded elements")


@router.post("/render", response_model=Dict[str, Any])
async def render_dynamic_spa_page(payload: DynamicRenderRequest):
    """Renders a JavaScript-heavy web application in headless Chromium and returns fully hydrated HTML."""
    return await DynamicBrowserService.fetch_dynamic_page(
        url=str(payload.url),
        wait_for_selector=payload.wait_for_selector,
        timeout_seconds=payload.timeout_seconds,
        scroll_to_bottom=payload.scroll_to_bottom
    )