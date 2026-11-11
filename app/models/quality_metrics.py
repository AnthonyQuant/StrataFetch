from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FieldValidationResult(BaseModel):
    field_name: str
    is_valid: bool
    missing: bool = False
    error: Optional[str] = None
    raw_value: Optional[Any] = None


class RecordValidationReport(BaseModel):
    record_index: int
    is_valid: bool
    missing_fields: List[str] = Field(default_factory=list)
    invalid_fields: List[str] = Field(default_factory=list)
    field_details: Dict[str, FieldValidationResult] = Field(default_factory=dict)


class QualityReportSummary(BaseModel):
    total_pages_visited: int = Field(0, description="Total web pages fetched during job")
    total_records_extracted: int = Field(0, description="Raw records extracted before quality filtering")
    duplicate_records_detected: int = Field(0, description="Number of duplicate records removed")
    valid_records_count: int = Field(0, description="Records fully passing schema rules")
    invalid_records_count: int = Field(0, description="Records failing schema or missing required fields")
    total_missing_fields: int = Field(0, description="Total count of missing field instances across all records")
    extraction_success_rate: float = Field(0.0, description="Percentage of successfully fetched pages (0 - 100%)")
    schema_compliance_rate: float = Field(0.0, description="Percentage of extracted records meeting schema requirements (0 - 100%)")
    detailed_reports: List[RecordValidationReport] = Field(default_factory=list)