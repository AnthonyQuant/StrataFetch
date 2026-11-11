import csv
import io
import json
from enum import Enum
from typing import Any, Dict, List, Tuple


class ExportFormatEnum(str, Enum):
    JSON = "json"
    JSONL = "jsonl"
    CSV = "csv"
    EXCEL = "xlsx"
    PARQUET = "parquet"


class DataExporterService:
    """Exports extracted record collections into JSON, JSONL, CSV, Excel, and Parquet formats."""

    @classmethod
    def export_records(
        cls,
        records: List[Dict[str, Any]],
        export_format: ExportFormatEnum,
        filename_prefix: str = "stratafetch_export"
    ) -> Tuple[bytes, str, str]:
        """Converts records into requested format. Returns (file_bytes, media_type, filename)."""
        format_val = export_format.value.lower()

        if format_val == ExportFormatEnum.JSON.value:
            content = json.dumps(records, indent=2, ensure_ascii=False, default=str).encode("utf-8")
            media_type = "application/json"
            filename = f"{filename_prefix}.json"

        elif format_val == ExportFormatEnum.JSONL.value:
            lines = [json.dumps(r, ensure_ascii=False, default=str) for r in records]
            content = "\n".join(lines).encode("utf-8")
            media_type = "application/x-ndjson"
            filename = f"{filename_prefix}.jsonl"

        elif format_val == ExportFormatEnum.CSV.value:
            output = io.StringIO()
            if records:
                fieldnames = list(dict.fromkeys(k for r in records for k in r.keys()))
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                for r in records:
                    row = {k: json.dumps(v, default=str) if isinstance(v, (dict, list)) else v for k, v in r.items()}
                    writer.writerow(row)
            content = output.getvalue().encode("utf-8")
            media_type = "text/csv"
            filename = f"{filename_prefix}.csv"

        elif format_val in (ExportFormatEnum.EXCEL.value, ExportFormatEnum.PARQUET.value):
            import pandas as pd
            df = pd.DataFrame(records)
            output = io.BytesIO()

            if format_val == ExportFormatEnum.EXCEL.value:
                df.to_excel(output, index=False, engine="openpyxl")
                media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                filename = f"{filename_prefix}.xlsx"
            else:
                df.to_parquet(output, index=False, engine="pyarrow")
                media_type = "application/octet-stream"
                filename = f"{filename_prefix}.parquet"

            content = output.getvalue()

        else:
            raise ValueError(f"Unsupported export format: {export_format}")

        return content, media_type, filename