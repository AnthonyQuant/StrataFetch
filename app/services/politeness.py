import asyncio
import random
import time
from typing import Dict, Optional
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
import httpx


class PolitenessService:
    """Manages robots.txt parsing, per-domain rate limiting, and HTTP 429 backoff handling."""

    _robots_cache: Dict[str, RobotFileParser] = {}
    _last_request_times: Dict[str, float] = {}
    _domain_delays: Dict[str, float] = {}

    DEFAULT_USER_AGENT = "StrataFetch/1.0"
    DEFAULT_CRAWL_DELAY = 1.0  # Default seconds between requests if unspecified

    @classmethod
    def get_domain(cls, url: str) -> str:
        parsed = urlparse(url)
        return parsed.netloc.lower()

    @classmethod
    async def fetch_robots_txt(cls, url: str, user_agent: str = DEFAULT_USER_AGENT) -> Optional[RobotFileParser]:
        """Fetches, parses, and caches robots.txt rules for target domain."""
        domain = cls.get_domain(url)
        if domain in cls._robots_cache:
            return cls._robots_cache[domain]

        scheme = urlparse(url).scheme or "https"
        robots_url = f"{scheme}://{domain}/robots.txt"

        rfp = RobotFileParser()
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                res = await client.get(robots_url, headers={"User-Agent": user_agent})
                if res.status_code == 200:
                    rfp.parse(res.text.splitlines())
                else:
                    rfp.parse([])
        except Exception:
            rfp.parse([])

        cls._robots_cache[domain] = rfp

        delay = rfp.crawl_delay(user_agent) or rfp.crawl_delay("*")
        if delay:
            cls._domain_delays[domain] = float(delay)

        return rfp

    @classmethod
    async def is_allowed(cls, url: str, user_agent: str = DEFAULT_USER_AGENT) -> bool:
        """Verifies if fetching target URL is permitted under domain robots.txt rules."""
        rfp = await cls.fetch_robots_txt(url, user_agent)
        if rfp is None:
            return True
        return rfp.can_fetch(user_agent, url)

    @classmethod
    async def enforce_rate_limit(cls, url: str, custom_delay: Optional[float] = None):
        """Enforces per-domain request rate limits using asyncio.sleep."""
        domain = cls.get_domain(url)
        now = time.time()

        delay = custom_delay or cls._domain_delays.get(domain, cls.DEFAULT_CRAWL_DELAY)
        last_time = cls._last_request_times.get(domain, 0.0)

        elapsed = now - last_time
        if elapsed < delay:
            sleep_duration = delay - elapsed
            await asyncio.sleep(sleep_duration)

        cls._last_request_times[domain] = time.time()

    @classmethod
    def parse_retry_after(cls, response_headers: Dict[str, str]) -> Optional[float]:
        """Parses Retry-After header values (seconds) from HTTP 429 responses."""
        retry_header = response_headers.get("Retry-After") or response_headers.get("retry-after")
        if not retry_header:
            return None

        try:
            return float(retry_header)
        except ValueError:
            return 5.0

    @classmethod
    def get_backoff_delay(cls, attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
        """Calculates exponential backoff with randomized jitter."""
        exponential = base_delay * (2 ** (attempt - 1))
        jitter = random.uniform(0.5, 1.5)
        return min(exponential * jitter, max_delay)