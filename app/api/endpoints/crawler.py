from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, HttpUrl

from app.services.crawler import DeepCrawlerService
from app.services.http_client import HTTPClientService
from app.services.playwright_renderer import PlaywrightRendererService
from app.services.url_queue import URLQueueService

router = APIRouter(prefix="/api/crawler", tags=["Crawling Engine"])


class FetchPageRequest(BaseModel):
    url: HttpUrl = Field(..., description="Target webpage URL to crawl")
    timeout_seconds: Optional[int] = Field(30, ge=1, le=120)
    max_retries: Optional[int] = Field(3, ge=1, le=5)


class QuickCrawlRequest(BaseModel):
    base_url: HttpUrl = Field(..., description="Starting seed URL for crawl job")
    max_pages: int = Field(5, ge=1, le=50, description="Maximum number of pages to fetch")
    restrict_domain: bool = Field(True, description="Restrict crawling strictly to target domain")


class PlaywrightRenderRequest(BaseModel):
    url: HttpUrl = Field(..., description="JavaScript-heavy webpage URL to render")
    wait_selector: Optional[str] = Field(None, description="Optional CSS selector to wait for before capturing HTML")
    timeout_ms: Optional[int] = Field(30000, ge=5000, le=60000)


class DeepCrawlRequest(BaseModel):
    base_url: HttpUrl = Field(..., description="Seed URL for multi-page crawl")
    max_depth: int = Field(2, ge=1, le=5, description="Maximum link depth level to traverse")
    max_pages: int = Field(20, ge=1, le=100, description="Maximum total pages to crawl")
    restrict_domain: bool = Field(True, description="Restrict crawl strictly within seed domain boundary")
    force_playwright: bool = Field(False, description="Force headless Playwright rendering for every page")
    concurrency: int = Field(5, ge=1, le=10, description="Concurrent request limit")


@router.post("/fetch-single", response_model=Dict[str, Any])
async def fetch_single_page(payload: FetchPageRequest):
    result = await HTTPClientService.fetch_page(
        url=str(payload.url),
        timeout_seconds=payload.timeout_seconds,
        max_retries=payload.max_retries
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=f"Failed to fetch page: {result['error']}")
    return result


@router.post("/quick-crawl", response_model=Dict[str, Any])
async def execute_quick_crawl(payload: QuickCrawlRequest):
    seed_url = str(payload.base_url)
    queue = URLQueueService(base_url=seed_url, restrict_domain=payload.restrict_domain)
    await queue.add_url(seed_url)

    crawled_results: List[Dict[str, Any]] = []

    while not queue.pending_urls.empty() and len(crawled_results) < payload.max_pages:
        current_url = await queue.get_next_url()
        if not current_url:
            break

        res = await HTTPClientService.fetch_page(url=current_url, max_retries=2)
        crawled_results.append({
            "url": current_url,
            "status_code": res["status_code"],
            "success": res["success"],
            "content_length": res["content_length"]
        })

    return {
        "seed_url": seed_url,
        "total_crawled": len(crawled_results),
        "total_discovered": queue.total_discovered,
        "pages": crawled_results
    }


@router.post("/render-playwright", response_model=Dict[str, Any])
async def render_page_with_playwright(payload: PlaywrightRenderRequest):
    """Renders a JavaScript-heavy page using headless Chromium."""
    result = await PlaywrightRendererService.render_page(
        url=str(payload.url),
        wait_selector=payload.wait_selector,
        timeout_ms=payload.timeout_ms or 30000
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=f"Playwright rendering failed: {result['error']}")
    return result


@router.post("/deep-crawl", response_model=Dict[str, Any])
async def execute_deep_crawl(payload: DeepCrawlRequest):
    """Executes a multi-page crawl with depth control, link discovery, and Playwright rendering fallback."""
    crawler = DeepCrawlerService(
        seed_url=str(payload.base_url),
        max_depth=payload.max_depth,
        max_pages=payload.max_pages,
        restrict_domain=payload.restrict_domain,
        force_playwright=payload.force_playwright,
        concurrency=payload.concurrency
    )
    return await crawler.run_crawl()