import asyncio
from typing import Set, Optional
from urllib.parse import urlparse, urljoin, urlunparse


class URLQueueService:
    """Manages crawl queues, URL deduplication, domain boundaries, and concurrency limits."""

    def __init__(self, base_url: str, restrict_domain: bool = True, max_concurrent: int = 5):
        self.base_url = base_url
        self.base_domain = urlparse(base_url).netloc
        self.restrict_domain = restrict_domain
        self.visited_urls: Set[str] = set()
        self.pending_urls: asyncio.Queue[str] = asyncio.Queue()
        self.semaphore = asyncio.Semaphore(max_concurrent)

    @staticmethod
    def normalize_url(url: str) -> str:
        parsed = urlparse(url)
        clean_path = parsed.path.rstrip("/") if parsed.path != "/" else "/"
        return urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), clean_path, "", "", ""))

    def is_valid_url(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        if self.restrict_domain and parsed.netloc.lower() != self.base_domain.lower():
            return False
        return True

    async def add_url(self, url: str) -> bool:
        full_url = urljoin(self.base_url, url)
        normalized = self.normalize_url(full_url)

        if normalized not in self.visited_urls and self.is_valid_url(normalized):
            self.visited_urls.add(normalized)
            await self.pending_urls.put(normalized)
            return True
        return False

    async def get_next_url(self) -> Optional[str]:
        if self.pending_urls.empty():
            return None
        return await self.pending_urls.get()

    @property
    def total_discovered(self) -> int:
        return len(self.visited_urls)