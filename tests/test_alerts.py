import pytest
from app.services.alert_trigger import NotificationAlertTriggerService


@pytest.mark.asyncio
async def test_new_opportunity_alert():
    new_opp = {
        "title": "Data Science Intern",
        "organisation": "Strata AI",
        "deadline": "2026-12-31",
        "application_url": "https://example.com/apply"
    }

    result = await NotificationAlertTriggerService.process_opportunity_changes(
        old_record=None,
        new_record=new_opp
    )

    assert result["alert_triggered"] is True
    assert result["event_type"] == "OPPORTUNITY_DISCOVERED"


@pytest.mark.asyncio
async def test_deadline_changed_alert():
    old_opp = {"title": "Data Science Intern", "deadline": "2026-12-01"}
    new_opp = {"title": "Data Science Intern", "deadline": "2026-12-15"}

    result = await NotificationAlertTriggerService.process_opportunity_changes(
        old_record=old_opp,
        new_record=new_opp
    )

    assert result["alert_triggered"] is True
    assert result["event_type"] == "DEADLINE_CHANGED"