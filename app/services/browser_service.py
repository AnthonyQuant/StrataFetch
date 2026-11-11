import logging
from typing import Any, Dict, Optional
from playwright.async_api import async_playwright
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.services.security import SecurityService

logger = logging.getLogger(__name__)


class DynamicBrowserService:
    @staticmethod
    async def render_page(
        url: str,
        wait_for_selector: Optional[str] = None,
        timeout_seconds: int = 30,
        scroll_to_bottom: bool = False,
    ) -> Dict[str, Any]:
        """Hydrates dynamic JS pages using Playwright async API with strict error isolation and resource teardown."""
        # 1. SSRF & Scheme Protection (Layer B)
        is_safe, reason = SecurityService.validate_url_safety(url)
        if not is_safe:
            return {
                "url": url,
                "status_code": 400,
                "html_content": "",
                "success": False,
                "error": f"SECURITY_RESTRICTION: {reason}",
            }

        timeout_ms = timeout_seconds * 1000

        async with async_playwright() as p:
            # 2. Browser Launch Stage (Isolated Exception Handling)
            try:
                browser = await p.chromium.launch(headless=True)
            except Exception as launch_err:
                logger.error(f"Chromium launch failure: {launch_err}")
                return {
                    "url": url,
                    "status_code": 500,
                    "html_content": "",
                    "success": False,
                    "error": (
                        f"BROWSER_LAUNCH_ERROR: Headless Chromium binary missing or failed to start. "
                        f"Details: {str(launch_err)}"
                    ),
                }

            # 3. Execution Stage with Guaranteed Resource Cleanup
            try:
                context = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    )
                )
                page = await context.new_page()

                # Navigation
                response = await page.goto(
                    url, wait_until="networkidle", timeout=timeout_ms
                )
                status_code = response.status if response else 200

                # Optional Scroll Trigger
                if scroll_to_bottom:
                    await page.evaluate(
                        "window.scrollTo(0, document.body.scrollHeight)"
                    )
                    await page.wait_for_timeout(1000)

                # 4. Selector Wait Stage (Separated from Browser Launch Errors)
                selector_warning = None
                if wait_for_selector:
                    try:
                        await page.wait_for_selector(
                            wait_for_selector, timeout=timeout_ms
                        )
                    except PlaywrightTimeoutError:
                        logger.warning(
                            f"Selector '{wait_for_selector}' timed out on {url}"
                        )
                        selector_warning = (
                            f"SELECTOR_TIMEOUT: Element '{wait_for_selector}' was not found within "
                            f"{timeout_seconds}s. Returning captured HTML up to timeout."
                        )

                html_content = await page.content()
                page_title = await page.title()

                return {
                    "url": url,
                    "title": page_title,
                    "status_code": status_code,
                    "html_content": html_content,
                    "content_length": len(html_content),
                    "success": True,
                    "warning": selector_warning,
                    "error": None,
                }

            except Exception as page_err:
                logger.error(f"Navigation error on {url}: {page_err}")
                return {
                    "url": url,
                    "status_code": 500,
                    "html_content": "",
                    "success": False,
                    "error": f"NAVIGATION_ERROR: {str(page_err)}",
                }
            finally:
                # Guaranteed cleanup
                await browser.close()


# Alias for backward compatibility
BrowserService = DynamicBrowserService