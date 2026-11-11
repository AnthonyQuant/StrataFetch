from typing import Any, Dict, Optional
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


class PlaywrightRendererService:
    """Headless browser rendering service for JavaScript-heavy webpages using Playwright."""

    @classmethod
    async def render_page(
        cls,
        url: str,
        wait_selector: Optional[str] = None,
        timeout_ms: int = 30000,
        wait_until: str = "networkidle"
    ) -> Dict[str, Any]:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 StrataFetch/1.0"
            )
            page = await context.new_page()

            try:
                response = await page.goto(url, timeout=timeout_ms, wait_until=wait_until)
                if wait_selector:
                    await page.wait_for_selector(wait_selector, timeout=timeout_ms)

                html_content = await page.content()
                status_code = response.status if response else 200

                return {
                    "url": page.url,
                    "status_code": status_code,
                    "html_content": html_content,
                    "content_length": len(html_content),
                    "rendered_by": "playwright",
                    "success": True,
                    "error": None
                }
            except PlaywrightTimeoutError as e:
                return {
                    "url": url,
                    "status_code": 408,
                    "html_content": "",
                    "content_length": 0,
                    "rendered_by": "playwright",
                    "success": False,
                    "error": f"Playwright Timeout: {str(e)}"
                }
            except Exception as e:
                return {
                    "url": url,
                    "status_code": 500,
                    "html_content": "",
                    "content_length": 0,
                    "rendered_by": "playwright",
                    "success": False,
                    "error": str(e)
                }
            finally:
                await browser.close()