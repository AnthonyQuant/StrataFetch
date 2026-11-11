import asyncio
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from app.services.http_client import HTTPClientService
from app.services.playwright_renderer import PlaywrightRendererService
from app.services.url_queue import URLQueueService


class DeepCrawlerService:
    """Multi-page crawler supporting depth control, pagination detection, and Playwright JS rendering fallback."""

    PAGINATION_PATTERNS = [
        re.compile(r"page[=/_-]?\d+", re.I),
        re.compile(r"p[=/_-]?\d+", re.I),
        re.compile(r"next", re.I),
        re.compile(r"pagination", re.I),
    ]

    def __init__(
        self,
        seed_url: str,
        max_depth: int = 2,
        max_pages: int = 20,
        restrict_domain: bool = True,
        force_playwright: bool = False,
        concurrency: int = 5
    ):
        self.seed_url = seed_url
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.force_playwright = force_playwright
        self.queue = URLQueueService(base_url=seed_url, restrict_domain=restrict_domain, max_concurrent=concurrency)

    @classmethod
    def is_pagination_link(cls, href: str, text: str) -> bool:
        combined = f"{href} {text}"
        return any(pattern.search(combined) for pattern in cls.PAGINATION_PATTERNS)

    @staticmethod
    def extract_links(html_content: str, current_url: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html_content, "lxml")
        discovered: List[Dict[str, Any]] = []

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            text = a.get_text(strip=True)
            if not href or href.startswith("#") or href.startswith("javascript:"):
                continue

            full_url = urljoin(current_url, href)
            discovered.append({
                "url": full_url,
                "text": text,
                "is_pagination": DeepCrawlerService.is_pagination_link(href, text)
            })

        return discovered

    async def fetch_page_with_fallback(self, url: str) -> Dict[str, Any]:
        if self.force_playwright:
            return await PlaywrightRendererService.render_page(url)

        res = await HTTPClientService.fetch_page(url)
        # Automatic fallback to Playwright if HTTP response body is empty/minimal
        if res["success"] and len(res["html_content"].strip()) < 300:
            playwright_res = await PlaywrightRendererService.render_page(url)
            if playwright_res["success"] and len(playwright_res["html_content"]) > len(res["html_content"]):
                return playwright_res

        res["rendered_by"] = "httpx"
        return res

    async def run_crawl(self) -> Dict[str, Any]:
        await self.queue.add_url(self.seed_url)

        depth_map: Dict[str, int] = {URLQueueService.normalize_url(self.seed_url): 0}
        crawled_results: List[Dict[str, Any]] = []

        while not self.queue.pending_urls.empty() and len(crawled_results) < self.max_pages:
            current_url = await self.queue.get_next_url()
            if not current_url:
                break

            current_depth = depth_map.get(URLQueueService.normalize_url(current_url), 0)
            page_data = await self.fetch_page_with_fallback(current_url)

            discovered_links: List[Dict[str, Any]] = []
            if page_data["success"] and page_data["html_content"]:
                discovered_links = self.extract_links(page_data["html_content"], current_url)

                if current_depth < self.max_depth:
                    for link_info in discovered_links:
                        normalized = URLQueueService.normalize_url(link_info["url"])
                        added = await self.queue.add_url(link_info["url"])
                        if added:
                            depth_map[normalized] = current_depth + 1

            crawled_results.append({
                "url": current_url,
                "depth": current_depth,
                "status_code": page_data["status_code"],
                "success": page_data["success"],
                "rendered_by": page_data.get("rendered_by", "httpx"),
                "content_length": page_data["content_length"],
                "discovered_links_count": len(discovered_links),
                "error": page_data.get("error")
            })

        return {
            "seed_url": self.seed_url,
            "max_depth": self.max_depth,
            "total_crawled": len(crawled_results),
            "total_discovered": self.queue.total_discovered,
            "results": crawled_results
        }