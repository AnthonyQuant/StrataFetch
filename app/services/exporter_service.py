import csv
import io
import json
from typing import Any, Dict, List


class DataExporterService:
    """Converts extracted record collections into various structured output formats for download or pipeline consumption."""

    @staticmethod
    def to_json(records: List[Dict[str, Any]], indent: int = 2) -> str:
        """Serializes record list to formatted JSON string."""
        return json.dumps(records, indent=indent, default=str)

    @staticmethod
    def to_jsonl(records: List[Dict[str, Any]]) -> str:
        """Serializes record list to JSON Lines (JSONL) string format."""
        lines = [json.dumps(r, default=str) for r in records]
        return "\n".join(lines)

    @staticmethod
    def to_csv(records: List[Dict[str, Any]]) -> str:
        """Flattens and converts dictionary records into standard CSV format."""
        if not records:
            return ""

        output = io.StringIO()
        # Collect all unique field keys across records
        fieldnames = set()
        for r in records:
            fieldnames.update(r.keys())
        sorted_fieldnames = sorted(list(fieldnames))

        writer = csv.DictWriter(output, fieldnames=sorted_fieldnames)
        writer.writeheader()

        for r in records:
            # Flatten non-primitive values (lists/dicts) into JSON strings
            row = {}
            for k, v in r.items():
                if isinstance(v, (dict, list)):
                    row[k] = json.dumps(v, default=str)
                else:
                    row[k] = v
            writer.writerow(row)

        return output.getvalue()