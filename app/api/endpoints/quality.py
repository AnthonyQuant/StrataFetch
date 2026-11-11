from typing import Any, Dict, List, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.models.extraction_profile import FieldExtractionRule
from app.models.quality_metrics import QualityReportSummary
from app.services.quality_reporter import DataQualityReporterService

router = APIRouter(prefix="/api/quality", tags=["Data Quality & Schema Validation"])


class QualityAuditRequest(BaseModel):
    records: List[Dict[str, Any]] = Field(..., description="Extracted records to validate")
    rules: List[FieldExtractionRule] = Field(..., description="Schema rules to evaluate against")
    total_pages_visited: int = Field(1, ge=1)
    successful_pages_visited: int = Field(1, ge=0)
    unique_keys: Optional[List[str]] = Field(None, description="Keys to enforce deduplication")


@router.post("/audit", response_model=QualityReportSummary)
async def audit_data_quality(payload: QualityAuditRequest):
    """Evaluates raw records against schema rules and returns a data quality report."""
    return DataQualityReporterService.generate_quality_report(
        records=payload.records,
        rules=payload.rules,
        total_pages_visited=payload.total_pages_visited,
        successful_pages_visited=payload.successful_pages_visited,
        unique_keys=payload.unique_keys
    )