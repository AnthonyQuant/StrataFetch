from typing import Any, Dict, List, Optional
from app.models.extraction_profile import FieldExtractionRule, DataTypeEnum
from app.models.quality_metrics import (
    FieldValidationResult,
    RecordValidationReport,
    QualityReportSummary
)
from app.services.normalizers import DataNormalizerService


class DataQualityReporterService:
    """Validates extracted data records against profile schemas and calculates data quality metrics."""

    @staticmethod
    def validate_field_type(val: Any, expected_type: DataTypeEnum) -> bool:
        if val is None:
            return True

        if expected_type == DataTypeEnum.STRING:
            return isinstance(val, str)
        elif expected_type in (DataTypeEnum.DECIMAL, DataTypeEnum.FLOAT):
            if isinstance(val, (int, float)):
                return True
            if isinstance(val, dict) and "amount" in val:
                return isinstance(val["amount"], (int, float))
            try:
                float(str(val))
                return True
            except ValueError:
                return False
        elif expected_type == DataTypeEnum.INTEGER:
            if isinstance(val, int):
                return True
            try:
                int(str(val))
                return True
            except ValueError:
                return False
        elif expected_type == DataTypeEnum.BOOLEAN:
            if isinstance(val, bool):
                return True
            return str(val).lower() in ("true", "false", "1", "0")
        elif expected_type == DataTypeEnum.URL:
            s_val = str(val)
            return s_val.startswith("http://") or s_val.startswith("https://") or s_val.startswith("/")
        elif expected_type == DataTypeEnum.DATETIME:
            return isinstance(val, str) and len(val) >= 8

        return True

    @classmethod
    def validate_single_record(
        cls,
        index: int,
        record: Dict[str, Any],
        rules: List[FieldExtractionRule]
    ) -> RecordValidationReport:
        missing_fields: List[str] = []
        invalid_fields: List[str] = []
        field_details: Dict[str, FieldValidationResult] = {}
        record_is_valid = True

        for rule in rules:
            val = record.get(rule.field_name)
            is_missing = DataNormalizerService.coerce_null(val) is None

            if is_missing:
                if rule.required:
                    missing_fields.append(rule.field_name)
                    record_is_valid = False
                    field_details[rule.field_name] = FieldValidationResult(
                        field_name=rule.field_name,
                        is_valid=False,
                        missing=True,
                        error="Required field is missing",
                        raw_value=val
                    )
                else:
                    field_details[rule.field_name] = FieldValidationResult(
                        field_name=rule.field_name,
                        is_valid=True,
                        missing=True,
                        raw_value=val
                    )
            else:
                type_ok = cls.validate_field_type(val, rule.data_type)
                if not type_ok:
                    invalid_fields.append(rule.field_name)
                    record_is_valid = False
                    field_details[rule.field_name] = FieldValidationResult(
                        field_name=rule.field_name,
                        is_valid=False,
                        missing=False,
                        error=f"Value fails type check for {rule.data_type.value}",
                        raw_value=val
                    )
                else:
                    field_details[rule.field_name] = FieldValidationResult(
                        field_name=rule.field_name,
                        is_valid=True,
                        missing=False,
                        raw_value=val
                    )

        return RecordValidationReport(
            record_index=index,
            is_valid=record_is_valid,
            missing_fields=missing_fields,
            invalid_fields=invalid_fields,
            field_details=field_details
        )

    @classmethod
    def generate_quality_report(
        cls,
        records: List[Dict[str, Any]],
        rules: List[FieldExtractionRule],
        total_pages_visited: int = 1,
        successful_pages_visited: int = 1,
        unique_keys: Optional[List[str]] = None
    ) -> QualityReportSummary:
        deduped = DataNormalizerService.deduplicate_records(records, unique_keys=unique_keys)
        duplicate_count = len(records) - len(deduped)

        detailed_reports: List[RecordValidationReport] = []
        valid_records_count = 0
        invalid_records_count = 0
        total_missing_fields = 0

        for idx, rec in enumerate(deduped, start=1):
            rep = cls.validate_single_record(idx, rec, rules)
            detailed_reports.append(rep)
            total_missing_fields += len(rep.missing_fields)

            if rep.is_valid:
                valid_records_count += 1
            else:
                invalid_records_count += 1

        total_records = len(deduped)
        schema_compliance = (valid_records_count / total_records * 100.0) if total_records > 0 else 0.0
        success_rate = (successful_pages_visited / total_pages_visited * 100.0) if total_pages_visited > 0 else 0.0

        return QualityReportSummary(
            total_pages_visited=total_pages_visited,
            total_records_extracted=len(records),
            duplicate_records_detected=duplicate_count,
            valid_records_count=valid_records_count,
            invalid_records_count=invalid_records_count,
            total_missing_fields=total_missing_fields,
            extraction_success_rate=round(success_rate, 2),
            schema_compliance_rate=round(schema_compliance, 2),
            detailed_reports=detailed_reports
        )

    @classmethod
    def evaluate_quality(
        cls,
        records: List[Dict[str, Any]],
        required_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Evaluates quality score dictionary for unit testing assertions."""
        req_set = set(required_fields or [])
        sample_record_keys = list(records[0].keys()) if records else list(req_set)

        rules = [
            FieldExtractionRule(
                field_name=k,
                rule_type="css_selector",
                expression=k,
                data_type=DataTypeEnum.STRING,
                required=(k in req_set)
            )
            for k in sample_record_keys
        ]

        summary = cls.generate_quality_report(records, rules)
        valid_cnt = summary.valid_records_count
        tot_cnt = summary.total_records_extracted
        completeness = (valid_cnt / tot_cnt * 100.0) if tot_cnt > 0 else 0.0

        return {
            "total_records": tot_cnt,
            "valid_records": valid_cnt,
            "invalid_records": summary.invalid_records_count,
            "completeness_score": round(completeness, 2),
            "schema_compliance_rate": summary.schema_compliance_rate
        }


# Backwards compatibility alias
DataQualityService = DataQualityReporterService