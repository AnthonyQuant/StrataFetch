from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class HealthStatusEnum(str, Enum):
    HEALTHY = "Healthy"
    DEGRADED = "Degraded"
    BROKEN = "Broken"


class ProfileHealthReport(BaseModel):
    profile_name: str
    status: HealthStatusEnum
    current_success_rate: float = Field(..., description="Success rate % of current extraction run")
    previous_success_rate: float = Field(..., description="Historical baseline success rate %")
    records_expected: int = Field(..., description="Expected baseline record count based on historical runs")
    records_extracted: int = Field(..., description="Actual record count extracted in current run")
    yield_drop_percentage: float = Field(..., description="Percentage drop in record yield")
    warning_message: Optional[str] = None


class SelectorHealthService:
    """Monitors extraction profile yield metrics to detect DOM structure drift and broken selectors."""

    DEGRADED_THRESHOLD_PCT = 30.0  # >30% yield drop flags DEGRADED
    BROKEN_THRESHOLD_PCT = 70.0    # >70% yield drop flags BROKEN

    @classmethod
    def evaluate_profile_health(
        cls,
        profile_name: str,
        current_extracted_count: int,
        historical_expected_count: int,
        previous_success_rate: float = 98.2
    ) -> ProfileHealthReport:
        if historical_expected_count <= 0:
            current_success_rate = 100.0 if current_extracted_count > 0 else 0.0
            return ProfileHealthReport(
                profile_name=profile_name,
                status=HealthStatusEnum.HEALTHY,
                current_success_rate=current_success_rate,
                previous_success_rate=previous_success_rate,
                records_expected=historical_expected_count,
                records_extracted=current_extracted_count,
                yield_drop_percentage=0.0,
                warning_message=None
            )

        yield_ratio = current_extracted_count / historical_expected_count
        current_success_rate = round(min(yield_ratio * 100.0, 100.0), 1)
        yield_drop = round(max(0.0, (1.0 - yield_ratio) * 100.0), 1)

        if yield_drop >= cls.BROKEN_THRESHOLD_PCT:
            status = HealthStatusEnum.BROKEN
            msg = f"Critical Failure: Possible website structure change detected. Record yield dropped by {yield_drop}%."
        elif yield_drop >= cls.DEGRADED_THRESHOLD_PCT:
            status = HealthStatusEnum.DEGRADED
            msg = f"Possible website structure change detected. Extraction yield dropped from {historical_expected_count} to {current_extracted_count} records."
        else:
            status = HealthStatusEnum.HEALTHY
            msg = None

        return ProfileHealthReport(
            profile_name=profile_name,
            status=status,
            current_success_rate=current_success_rate,
            previous_success_rate=previous_success_rate,
            records_expected=historical_expected_count,
            records_extracted=current_extracted_count,
            yield_drop_percentage=yield_drop,
            warning_message=msg
        )