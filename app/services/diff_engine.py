import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FieldChange(BaseModel):
    field_name: str
    previous_value: Optional[Any] = None
    current_value: Optional[Any] = None
    change_type: str  # "modified", "price_increased", "price_decreased", "price_unchanged"
    delta: Optional[float] = None


class RecordDiffResult(BaseModel):
    record_key: str
    status: str  # "new", "removed", "modified", "unchanged"
    previous_record: Optional[Dict[str, Any]] = None
    current_record: Optional[Dict[str, Any]] = None
    changes: List[FieldChange] = Field(default_factory=list)


class SessionDiffReport(BaseModel):
    previous_session_id: str
    current_session_id: str
    profile_name: str
    total_previous_records: int
    total_current_records: int
    new_records_count: int
    removed_records_count: int
    modified_records_count: int
    unchanged_records_count: int
    price_increases_count: int
    price_decreases_count: int
    record_diffs: List[RecordDiffResult]


class DiffEngineService:
    """Compares historical snapshot sessions to detect new, removed, modified records and price movements."""

    @staticmethod
    def extract_numeric_val(val: Any) -> Optional[float]:
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, dict) and "amount" in val:
            try:
                return float(val["amount"])
            except (ValueError, TypeError):
                return None
        if isinstance(val, str):
            clean = re.sub(r'[^\d.-]', '', val)
            try:
                return float(clean)
            except ValueError:
                return None
        return None

    @classmethod
    def compare_field_values(cls, field_name: str, prev_val: Any, curr_val: Any) -> Optional[FieldChange]:
        if prev_val == curr_val:
            return None

        is_price_field = any(term in field_name.lower() for term in ["price", "cost", "amount", "fee", "rate"])

        prev_num = cls.extract_numeric_val(prev_val)
        curr_num = cls.extract_numeric_val(curr_val)

        if is_price_field and prev_num is not None and curr_num is not None:
            delta = round(curr_num - prev_num, 2)
            if curr_num > prev_num:
                change_type = "price_increased"
            elif curr_num < prev_num:
                change_type = "price_decreased"
            else:
                change_type = "price_unchanged"

            return FieldChange(
                field_name=field_name,
                previous_value=prev_val,
                current_value=curr_val,
                change_type=change_type,
                delta=delta
            )

        return FieldChange(
            field_name=field_name,
            previous_value=prev_val,
            current_value=curr_val,
            change_type="modified",
            delta=None
        )

    @classmethod
    def compare_sessions(
        cls,
        previous_session_id: str,
        current_session_id: str,
        profile_name: str,
        previous_records: List[Dict[str, Any]],
        current_records: List[Dict[str, Any]],
        primary_key_field: Optional[str] = None
    ) -> SessionDiffReport:

        def get_record_key(rec: Dict[str, Any], idx: int) -> str:
            if primary_key_field and primary_key_field in rec and rec[primary_key_field]:
                return str(rec[primary_key_field]).strip().lower()
            for fallback in ["product_name", "title", "name", "url", "id"]:
                if fallback in rec and rec[fallback]:
                    return str(rec[fallback]).strip().lower()
            return f"record_idx_{idx}"

        prev_map: Dict[str, Dict[str, Any]] = {get_record_key(r, i): r for i, r in enumerate(previous_records, 1)}
        curr_map: Dict[str, Dict[str, Any]] = {get_record_key(r, i): r for i, r in enumerate(current_records, 1)}

        all_keys = list(dict.fromkeys(list(prev_map.keys()) + list(curr_map.keys())))

        record_diffs: List[RecordDiffResult] = []
        new_count = 0
        removed_count = 0
        modified_count = 0
        unchanged_count = 0
        price_increases = 0
        price_decreases = 0

        for key in all_keys:
            in_prev = key in prev_map
            in_curr = key in curr_map

            if in_curr and not in_prev:
                new_count += 1
                record_diffs.append(RecordDiffResult(
                    record_key=key,
                    status="new",
                    previous_record=None,
                    current_record=curr_map[key],
                    changes=[]
                ))
            elif in_prev and not in_curr:
                removed_count += 1
                record_diffs.append(RecordDiffResult(
                    record_key=key,
                    status="removed",
                    previous_record=prev_map[key],
                    current_record=None,
                    changes=[]
                ))
            else:
                prev_rec = prev_map[key]
                curr_rec = curr_map[key]
                all_fields = set(list(prev_rec.keys()) + list(curr_rec.keys()))

                changes: List[FieldChange] = []
                for field in all_fields:
                    f_change = cls.compare_field_values(field, prev_rec.get(field), curr_rec.get(field))
                    if f_change:
                        changes.append(f_change)
                        if f_change.change_type == "price_increased":
                            price_increases += 1
                        elif f_change.change_type == "price_decreased":
                            price_decreases += 1

                if changes:
                    modified_count += 1
                    record_diffs.append(RecordDiffResult(
                        record_key=key,
                        status="modified",
                        previous_record=prev_rec,
                        current_record=curr_rec,
                        changes=changes
                    ))
                else:
                    unchanged_count += 1
                    record_diffs.append(RecordDiffResult(
                        record_key=key,
                        status="unchanged",
                        previous_record=prev_rec,
                        current_record=curr_rec,
                        changes=[]
                    ))

        return SessionDiffReport(
            previous_session_id=previous_session_id,
            current_session_id=current_session_id,
            profile_name=profile_name,
            total_previous_records=len(previous_records),
            total_current_records=len(current_records),
            new_records_count=new_count,
            removed_records_count=removed_count,
            modified_records_count=modified_count,
            unchanged_records_count=unchanged_count,
            price_increases_count=price_increases,
            price_decreases_count=price_decreases,
            record_diffs=record_diffs
        )