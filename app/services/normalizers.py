import hashlib
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin


class DataNormalizerService:
    """Standardizes messy raw scraped data into clean, structured data types."""

    CURRENCY_REGEX = re.compile(
        r'(?P<symbol>[₦$€£¥₹R$]|\b[A-Z]{3}\b)?\s*(?P<amount>[\d,]+(?:\.\d+)?)\s*(?P<code_suffix>\b[A-Z]{3}\b)?',
        re.IGNORECASE
    )

    SYMBOL_MAP = {
        "₦": "NGN",
        "$": "USD",
        "€": "EUR",
        "£": "GBP",
        "¥": "JPY",
        "₹": "INR"
    }

    @staticmethod
    def normalize_string(raw_val: Optional[str]) -> Optional[str]:
        """Strips outer whitespace and condenses internal tabs, newlines, and multi-spaces."""
        if not raw_val or not isinstance(raw_val, str):
            return None
        cleaned = re.sub(r'\s+', ' ', raw_val).strip()
        return cleaned if cleaned else None

    @staticmethod
    def normalize_url(raw_url: Optional[str], base_url: Optional[str] = None) -> Optional[str]:
        """Resolves relative URL paths against a target base domain URL."""
        if not raw_url or not isinstance(raw_url, str):
            return None
        cleaned = raw_url.strip()
        if not cleaned:
            return None
        if base_url:
            return urljoin(base_url, cleaned)
        return cleaned

    @classmethod
    def normalize_currency(cls, raw_val: Optional[str]) -> Optional[Dict[str, Any]]:
        """Parses currency strings like '₦25,000', '25000 NGN', 'NGN 25,000', '$1,299.99'."""
        if not raw_val or not isinstance(raw_val, str):
            return None

        cleaned_text = raw_val.strip()
        if not cleaned_text:
            return None

        match = cls.CURRENCY_REGEX.search(cleaned_text)
        if not match:
            digits_only = re.sub(r'[^\d.]', '', cleaned_text)
            try:
                amount = Decimal(digits_only)
                return {"amount": float(amount), "amount_decimal": str(amount), "currency": "UNKNOWN"}
            except (InvalidOperation, ValueError):
                return None

        amount_str = match.group("amount").replace(",", "")
        try:
            amount = Decimal(amount_str)
        except (InvalidOperation, ValueError):
            return None

        raw_code = (
            match.group("code_suffix") or
            match.group("symbol") or
            "UNKNOWN"
        ).upper().strip()

        currency_code = cls.SYMBOL_MAP.get(raw_code, raw_code)

        return {
            "amount": float(amount),
            "amount_decimal": str(amount),
            "currency": currency_code
        }

    @staticmethod
    def normalize_date(raw_val: Optional[str]) -> Optional[str]:
        """Converts raw date string representations into standard ISO 8601 format (YYYY-MM-DD)."""
        if not raw_val or not isinstance(raw_val, str):
            return None

        cleaned = raw_val.strip()
        if not cleaned:
            return None

        date_formats = [
            "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y",
            "%B %d, %Y", "%b %d, %Y", "%d %B %Y", "%d %b %Y",
            "%Y/%m/%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"
        ]

        cleaned_ordinals = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', cleaned)

        for fmt in date_formats:
            try:
                dt = datetime.strptime(cleaned_ordinals, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

        return None

    @staticmethod
    def coerce_null(raw_val: Any) -> Any:
        """Transforms empty strings, whitespace-only strings, or 'null'/'n/a' literals to None."""
        if raw_val is None:
            return None
        if isinstance(raw_val, str):
            cleaned = raw_val.strip()
            if not cleaned or cleaned.lower() in ("null", "n/a", "none", "undefined", "-", "nan"):
                return None
            return cleaned
        return raw_val

    @classmethod
    def normalize_record(cls, record: Dict[str, Any]) -> Dict[str, Any]:
        """Applies normalization transformers across a record dictionary."""
        normalized: Dict[str, Any] = {}
        for key, val in record.items():
            coerced = cls.coerce_null(val)
            if coerced is None:
                normalized[key] = None
                continue

            key_lower = key.lower()
            if any(term in key_lower for term in ["price", "cost", "amount", "salary", "fee"]):
                curr_res = cls.normalize_currency(str(coerced))
                normalized[key] = curr_res if curr_res else coerced
            elif any(term in key_lower for term in ["date", "time", "deadline", "created", "updated"]):
                date_res = cls.normalize_date(str(coerced))
                normalized[key] = date_res if date_res else coerced
            else:
                normalized[key] = coerced

        return normalized

    @classmethod
    def deduplicate_records(cls, records: List[Dict[str, Any]], unique_keys: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Deduplicates a collection of record dicts based on target key fields or total content hash."""
        seen_hashes = set()
        unique_records = []

        for record in records:
            if unique_keys:
                key_tuple = tuple(str(record.get(k, "")).strip().lower() for k in unique_keys)
                record_hash = hashlib.md5(":".join(key_tuple).encode("utf-8")).hexdigest()
            else:
                sorted_items = sorted((k, str(v)) for k, v in record.items())
                record_hash = hashlib.md5(str(sorted_items).encode("utf-8")).hexdigest()

            if record_hash not in seen_hashes:
                seen_hashes.add(record_hash)
                unique_records.append(record)

        return unique_records


# Backwards compatibility alias
NormalizerService = DataNormalizerService