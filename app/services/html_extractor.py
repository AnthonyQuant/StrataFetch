from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup
from lxml import etree

from app.models.extraction_profile import FieldExtractionRule
from app.services.parser_rules import ParserRuleService


class HTMLExtractorService:
    """Extracts page metadata, structured HTML tables, links, and user rules from raw HTML."""

    @staticmethod
    def extract_page_metadata(soup: BeautifulSoup) -> Dict[str, Any]:
        title = soup.title.string.strip() if soup.title and soup.title.string else None

        meta_data: Dict[str, str] = {}
        for meta in soup.find_all("meta"):
            name = meta.get("name") or meta.get("property")
            content = meta.get("content")
            if name and content:
                meta_data[name.lower()] = content.strip()

        return {
            "title": title,
            "meta_tags": meta_data,
            "og_title": meta_data.get("og:title", title),
            "og_description": meta_data.get("og:description", meta_data.get("description")),
            "og_image": meta_data.get("og:image"),
        }

    @staticmethod
    def extract_html_tables(soup: BeautifulSoup) -> List[Dict[str, Any]]:
        tables_data: List[Dict[str, Any]] = []

        for index, table in enumerate(soup.find_all("table")):
            headers: List[str] = []
            thead = table.find("thead")
            if thead:
                headers = [th.get_text(strip=True) for th in thead.find_all(["th", "td"])]
            elif table.find("tr"):
                first_row = table.find("tr")
                headers = [cell.get_text(strip=True) for cell in first_row.find_all(["th", "td"])]

            rows: List[List[str]] = []
            tbody = table.find("tbody") or table
            for tr in tbody.find_all("tr"):
                cells = [cell.get_text(strip=True) for cell in tr.find_all(["td", "th"])]
                if cells and cells != headers:
                    rows.append(cells)

            tables_data.append({
                "table_index": index + 1,
                "headers": headers,
                "row_count": len(rows),
                "rows": rows[:10]
            })

        return tables_data

    @staticmethod
    def extract_page_links(soup: BeautifulSoup) -> List[Dict[str, str]]:
        links: List[Dict[str, str]] = []
        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href").strip()
            text = anchor.get_text(strip=True)
            if href and not href.startswith("#") and not href.startswith("javascript:"):
                links.append({"href": href, "text": text})
        return links

    @classmethod
    def extract_field_value(cls, element: Any, rule: FieldExtractionRule) -> Optional[Any]:
        try:
            tree = etree.HTML(str(element))
        except Exception:
            tree = None
        return ParserRuleService.extract_field_value(element, tree, rule)

    @classmethod
    def extract(
        cls,
        html_content: str,
        container_selector: Optional[str] = None,
        rules: Optional[List[FieldExtractionRule]] = None
    ) -> List[Dict[str, Any]]:
        if not html_content or not rules:
            return []

        soup = BeautifulSoup(html_content, "lxml")
        records: List[Dict[str, Any]] = []

        if container_selector:
            containers = soup.select(container_selector)
        else:
            containers = [soup.body or soup]

        for container in containers:
            record: Dict[str, Any] = {}
            for rule in rules:
                record[rule.field_name] = cls.extract_field_value(container, rule)
            records.append(record)

        return records

    @classmethod
    def process_html_preview(
        cls,
        html_content: str,
        rules: Optional[List[FieldExtractionRule]] = None
    ) -> Dict[str, Any]:
        soup = BeautifulSoup(html_content, "lxml")

        metadata = cls.extract_page_metadata(soup)
        tables = cls.extract_html_tables(soup)
        links = cls.extract_page_links(soup)

        rule_results: Dict[str, Any] = {}
        if rules:
            rule_results = ParserRuleService.apply_profile_rules(html_content, rules)

        return {
            "metadata": metadata,
            "tables": tables,
            "links_count": len(links),
            "sample_links": links[:15],
            "extracted_fields": rule_results
        }