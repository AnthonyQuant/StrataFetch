from typing import Any, Dict, List, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.services.normalizers import DataNormalizerService

router = APIRouter(prefix="/api/normalizer", tags=["Data Normalization Engine"])


class CurrencyNormalizeRequest(BaseModel):
    raw_value: str = Field(..., description="Raw monetary text (e.g. '₦25,000', '25000 NGN', '$1,299.99')")


class DateNormalizeRequest(BaseModel):
    raw_value: str = Field(..., description="Raw date string (e.g. 'October 24, 2026', '24/10/2026')")


class CleanRecordRequest(BaseModel):
    record: Dict[str, Any] = Field(..., description="Key-value dictionary of extracted raw fields")


class DeduplicateRequest(BaseModel):
    records: List[Dict[str, Any]] = Field(..., description="List of extracted record objects")
    unique_keys: Optional[List[str]] = Field(None, description="Field keys to enforce uniqueness (e.g. ['product_name', 'url'])")


@router.post("/currency", response_model=Dict[str, Any])
async def normalize_currency_endpoint(payload: CurrencyNormalizeRequest):
    result = DataNormalizerService.normalize_currency(payload.raw_value)
    return {"raw": payload.raw_value, "normalized": result}


@router.post("/date", response_model=Dict[str, Any])
async def normalize_date_endpoint(payload: DateNormalizeRequest):
    result = DataNormalizerService.normalize_date(payload.raw_value)
    return {"raw": payload.raw_value, "normalized_iso": result}


@router.post("/clean-record", response_model=Dict[str, Any])
async def clean_record_endpoint(payload: CleanRecordRequest):
    result = DataNormalizerService.normalize_record(payload.record)
    return {"original": payload.record, "cleaned": result}


@router.post("/deduplicate", response_model=Dict[str, Any])
async def deduplicate_endpoint(payload: DeduplicateRequest):
    unique_list = DataNormalizerService.deduplicate_records(payload.records, payload.unique_keys)
    return {
        "total_input": len(payload.records),
        "total_unique": len(unique_list),
        "duplicates_removed": len(payload.records) - len(unique_list),
        "records": unique_list
    }