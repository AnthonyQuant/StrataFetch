import asyncio
import logging
from typing import Any, Dict, List, Optional
from app.services.webhook_service import WebhookService

logger = logging.getLogger(__name__)


class NotificationAlertTriggerService:
    """Evaluates extracted record changes and dispatches automated alerts for critical events."""

    @classmethod
    async def process_opportunity_changes(
        cls,
        old_record: Optional[Dict[str, Any]],
        new_record: Dict[str, Any],
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Detects new opportunities or deadline modifications and dispatches alerts."""
        event_type = None
        alert_payload = {}

        # Scenario 1: Newly Discovered Opportunity
        if old_record is None:
            event_type = "OPPORTUNITY_DISCOVERED"
            alert_payload = {
                "event": event_type,
                "title": new_record.get("title"),
                "organisation": new_record.get("organisation"),
                "deadline": new_record.get("deadline"),
                "url": new_record.get("application_url"),
                "message": f"New opportunity listed: {new_record.get('title')} at {new_record.get('organisation')}"
            }

        # Scenario 2: Modified Deadline
        elif old_record.get("deadline") != new_record.get("deadline"):
            event_type = "DEADLINE_CHANGED"
            alert_payload = {
                "event": event_type,
                "title": new_record.get("title"),
                "organisation": new_record.get("organisation"),
                "previous_deadline": old_record.get("deadline"),
                "new_deadline": new_record.get("deadline"),
                "url": new_record.get("application_url"),
                "message": f"Deadline updated for {new_record.get('title')}: {old_record.get('deadline')} ➔ {new_record.get('deadline')}"
            }

        if event_type and webhook_url:
            dispatch_result = await WebhookService.dispatch_webhook(
                target_url=webhook_url,
                payload=alert_payload
            )
            return {
                "alert_triggered": True,
                "event_type": event_type,
                "webhook_dispatched": dispatch_result.get("success", False),
                "payload": alert_payload
            }

        return {
            "alert_triggered": event_type is not None,
            "event_type": event_type,
            "webhook_dispatched": False,
            "payload": alert_payload
        }