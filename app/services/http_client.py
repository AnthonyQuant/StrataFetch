import asyncio
from typing import Any, Dict, Optional
import httpx
from app.config import settings
from app.services.politeness import PolitenessService
from app.services.security import SecurityService


class HTTPClientService:
    """Asynchronous HTTP fetcher featuring SSRF validation, politeness (robots.txt & rate limits), retries, and backoff."""

    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 StrataFetch/1.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    @classmethod
    async def fetch_page(
        cls,
        url: str,
        timeout_seconds: Optional[int] = None,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        custom_headers: Optional[Dict[str, str]] = None,
        ignore_robots_txt: bool = False
    ) -> Dict[str, Any]:
        # 1. SSRF Safety Check on initial URL
        is_safe, reason = SecurityService.validate_url_safety(url)
        if not is_safe:
            return {
                "url": url,
                "status_code": 400,
                "headers": {},
                "html_content": "",
                "content_length": 0,
                "attempts": 0,
                "success": False,
                "error": f"SSRF Security Restriction: {reason}"
            }

        headers = {**cls.DEFAULT_HEADERS, **(custom_headers or {})}
        user_agent = headers.get("User-Agent", cls.DEFAULT_HEADERS["User-Agent"])

        # 2. Robots.txt Compliance Check
        if not ignore_robots_txt:
            allowed = await PolitenessService.is_allowed(url, user_agent=user_agent)
            if not allowed:
                return {
                    "url": url,
                    "status_code": 403,
                    "headers": {},
                    "html_content": "",
                    "content_length": 0,
                    "attempts": 0,
                    "success": False,
                    "error": "Politeness Violation: Access to this URL is disallowed by the site's robots.txt policy."
                }

        # 3. Enforce Per-Domain Rate Limiting
        await PolitenessService.enforce_rate_limit(url)

        timeout = timeout_seconds or settings.HTTP_TIMEOUT_SECONDS

        async with httpx.AsyncClient(timeout=float(timeout), follow_redirects=True) as client:
            last_exception: Optional[Exception] = None

            for attempt in range(1, max_retries + 1):
                try:
                    response = await client.get(url, headers=headers)

                    # 4. Re-validate SSRF safety after following redirects
                    final_url_safe, final_reason = SecurityService.validate_url_safety(str(response.url))
                    if not final_url_safe:
                        return {
                            "url": str(response.url),
                            "status_code": 400,
                            "headers": {},
                            "html_content": "",
                            "content_length": 0,
                            "attempts": attempt,
                            "success": False,
                            "error": f"SSRF Security Restriction on redirect: {final_reason}"
                        }

                    response.raise_for_status()

                    return {
                        "url": str(response.url),
                        "status_code": response.status_code,
                        "headers": dict(response.headers),
                        "html_content": response.text,
                        "content_length": len(response.content),
                        "attempts": attempt,
                        "success": True,
                        "error": None
                    }
                except httpx.HTTPStatusError as exc:
                    last_exception = exc
                    if attempt < max_retries:
                        retry_delay = None
                        if exc.response is not None and exc.response.status_code == 429:
                            retry_delay = PolitenessService.parse_retry_after(dict(exc.response.headers))

                        sleep_duration = retry_delay or PolitenessService.get_backoff_delay(attempt, base_delay=backoff_factor)
                        await asyncio.sleep(sleep_duration)

                except httpx.RequestError as exc:
                    last_exception = exc
                    if attempt < max_retries:
                        sleep_duration = PolitenessService.get_backoff_delay(attempt, base_delay=backoff_factor)
                        await asyncio.sleep(sleep_duration)

            status_code = 500
            if hasattr(last_exception, "response") and last_exception.response is not None:
                status_code = last_exception.response.status_code

            return {
                "url": url,
                "status_code": status_code,
                "headers": {},
                "html_content": "",
                "content_length": 0,
                "attempts": max_retries,
                "success": False,
                "error": str(last_exception)
            }