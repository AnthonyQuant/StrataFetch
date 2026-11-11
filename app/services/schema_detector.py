from collections import Counter
import re
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup, Tag
from app.models.extraction_profile import DataTypeEnum, FieldExtractionRule


class SchemaDetectorService:
    """Analyzes HTML DOM structure to automatically identify repeating content containers and auto-suggest extraction field schemas."""

    @staticmethod
    def infer_data_type(sample_text: str) -> DataTypeEnum:
        text = sample_text.strip()
        if not text:
            return DataTypeEnum.STRING

        # Price pattern check
        if re.search(r'(?:[₦$€£¥₹]|\b[A-Z]{3}\b)?\s*\d+(?:,\d+)*(?:\.\d+)?', text, re.I):
            if any(term in text.lower() for term in ["price", "$", "₦", "€", "£", "usd", "ngn", "eur"]):
                return DataTypeEnum.DECIMAL

        # Date pattern check
        if re.search(
                r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|[A-Z][a-z]+\s+\d{1,2},\s+\d{4})\b',
                text):
            return DataTypeEnum.DATETIME

        # URL check
        if text.startswith(("http://", "https://", "/")):
            return DataTypeEnum.URL

        return DataTypeEnum.STRING

    @classmethod
    def find_repeating_containers(cls, soup: BeautifulSoup, min_repeats: int = 2) -> List[Dict[str, Any]]:
        """Finds DOM elements with repeating class names or structural wrappers (e.g. cards, list items, table rows)."""
        class_counts = Counter()
        for tag in soup.find_all(True):
            classes = tag.get("class")
            if classes and isinstance(classes, list):
                class_key = ".".join(classes)
                class_counts[class_key] += 1

        candidate_classes = [cls_name for cls_name, count in class_counts.items() if count >= min_repeats]

        containers: List[Dict[str, Any]] = []
        for cls_name in candidate_classes:
            matching_elements = soup.find_all(class_=cls_name.split("."))
            if matching_elements:
                containers.append({
                    "class_name": cls_name,
                    "count": len(matching_elements),
                    "sample_element": matching_elements[0]
                })

        table_rows = soup.find_all("tr")
        if len(table_rows) >= min_repeats:
            containers.append({
                "class_name": "tr",
                "count": len(table_rows),
                "sample_element": table_rows[0]
            })

        containers.sort(key=lambda x: x["count"], reverse=True)
        return containers

    @classmethod
    def auto_detect_schema(cls, html_content: str, container_selector: Optional[str] = None) -> Dict[str, Any]:
        """Analyzes HTML to auto-generate suggested field extraction rules."""
        soup = BeautifulSoup(html_content, "lxml")

        containers = cls.find_repeating_containers(soup)

        target_tag: Optional[Tag] = None
        detected_container_selector = container_selector

        if container_selector:
            matched = soup.select(container_selector)
            if matched:
                target_tag = matched[0]
        elif containers:
            top_container = containers[0]
            target_tag = top_container["sample_element"]
            cls_name = top_container["class_name"]
            detected_container_selector = "tr" if cls_name == "tr" else f".{cls_name}"
        else:
            target_tag = soup.body or soup

        suggested_rules: List[FieldExtractionRule] = []
        seen_fields = set()

        # 1. Detect Heading Title
        headings = target_tag.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        if headings:
            h_tag = headings[0]
            seen_fields.add("title")
            suggested_rules.append(FieldExtractionRule(
                field_name="title",
                rule_type="css_selector",
                expression=h_tag.name,
                data_type=DataTypeEnum.STRING,
                required=True
            ))

        # 2. Detect Hyperlinks
        links = target_tag.find_all("a", href=True)
        if links:
            seen_fields.add("application_url")
            suggested_rules.append(FieldExtractionRule(
                field_name="application_url",
                rule_type="css_selector",
                expression="a",
                attribute="href",
                data_type=DataTypeEnum.URL,
                required=True
            ))

        # 3. Detect Currency and Dates
        text_nodes = target_tag.find_all(string=True)
        for node in text_nodes:
            txt = node.strip()
            if not txt:
                continue
            inferred_type = cls.infer_data_type(txt)
            if inferred_type == DataTypeEnum.DECIMAL and "price" not in seen_fields:
                parent = node.parent
                parent_class = parent.get("class", []) if isinstance(parent, Tag) else []
                exp = f".{parent_class[0]}" if parent_class else (parent.name if isinstance(parent, Tag) else "span")
                seen_fields.add("price")
                suggested_rules.append(FieldExtractionRule(
                    field_name="price",
                    rule_type="css_selector",
                    expression=exp,
                    data_type=DataTypeEnum.DECIMAL,
                    required=False
                ))
            elif inferred_type == DataTypeEnum.DATETIME and "deadline" not in seen_fields:
                parent = node.parent
                parent_class = parent.get("class", []) if isinstance(parent, Tag) else []
                exp = f".{parent_class[0]}" if parent_class else (parent.name if isinstance(parent, Tag) else "span")
                seen_fields.add("deadline")
                suggested_rules.append(FieldExtractionRule(
                    field_name="deadline",
                    rule_type="css_selector",
                    expression=exp,
                    data_type=DataTypeEnum.DATETIME,
                    required=False
                ))

        # 4. Fallback Description Paragraphs
        paragraphs = target_tag.find_all("p")
        if paragraphs and "description" not in seen_fields:
            suggested_rules.append(FieldExtractionRule(
                field_name="description",
                rule_type="css_selector",
                expression="p",
                data_type=DataTypeEnum.STRING,
                required=False
            ))

        return {
            "detected_container_selector": detected_container_selector,
            "repeating_containers_found": len(containers),
            "suggested_rules": [rule.model_dump() for rule in suggested_rules]
        }