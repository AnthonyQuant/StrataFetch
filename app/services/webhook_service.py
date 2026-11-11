import logging
from typing import Any, Dict, Optional
import httpx

logger = logging.getLogger(__name__)


class WebhookDispatchService:
    """Asynchronously dispatches structured payload alerts and scraped records to external webhooks."""

    @classmethod
    async def send_webhook(
        cls,
        target_url: str,
        payload: Dict[str, Any],
        custom_headers: Optional[Dict[str, str]] = None,
        timeout: float = 10.0
    ) -> Dict[str, Any]:
        """Posts JSON payload to external webhook endpoint with status tracking."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "StrataFetch-WebhookDispatcher/1.0",
            **(custom_headers or {})
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(target_url, json=payload, headers=headers)
                success = response.status_code in (200, 201, 202, 204)
                return {
                    "target_url": target_url,
                    "status_code": response.status_code,
                    "success": success,
                    "response_text": response.text[:200],
                    "error": None if success else f"HTTP {response.status_code}"
                }
        except Exception as exc:
            logger.error(f"Failed to dispatch webhook to {target_url}: {str(exc)}")
            return {
                "target_url": target_url,
                "status_code": 500,
                "success": False,
                "response_text": "",
                "error": str(exc)
            }