import json
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup


class MetadataExtractorService:
    """Extracts structured JSON-LD schemas, Open Graph tags, and Twitter Card metadata from HTML DOM trees."""

    @classmethod
    def extract_json_ld(cls, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parses all embedded <script type="application/ld+json"> blocks."""
        schemas: List[Dict[str, Any]] = []

        for script in soup.find_all("script", type="application/ld+json"):
            if not script.string:
                continue
            try:
                data = json.loads(script.string.strip())
                if isinstance(data, list):
                    schemas.extend(data)
                elif isinstance(data, dict):
                    schemas.append(data)
            except json.JSONDecodeError:
                continue

        return schemas

    @classmethod
    def extract_open_graph(cls, soup: BeautifulSoup) -> Dict[str, str]:
        """Extracts Open Graph meta property tags (og:title, og:description, og:image, etc.)."""
        og_data: Dict[str, str] = {}

        for meta in soup.find_all("meta"):
            prop = meta.get("property") or meta.get("name") or ""
            content = meta.get("content") or ""

            if prop.startswith("og:") and content:
                key = prop[3:].replace(":", "_")
                og_data[key] = content.strip()

        return og_data

    @classmethod
    def extract_twitter_cards(cls, soup: BeautifulSoup) -> Dict[str, str]:
        """Extracts Twitter card meta tags (twitter:title, twitter:description, etc.)."""
        twitter_data: Dict[str, str] = {}

        for meta in soup.find_all("meta"):
            name = meta.get("name") or meta.get("property") or ""
            content = meta.get("content") or ""

            if name.startswith("twitter:") and content:
                key = name[8:].replace(":", "_")
                twitter_data[key] = content.strip()

        return twitter_data

    @classmethod
    def extract_all_metadata(cls, html_content: str) -> Dict[str, Any]:
        """Runs comprehensive metadata extraction across JSON-LD, Open Graph, and Twitter Cards."""
        soup = BeautifulSoup(html_content, "lxml")

        json_ld_list = cls.extract_json_ld(soup)
        og_tags = cls.extract_open_graph(soup)
        twitter_tags = cls.extract_twitter_cards(soup)

        has_metadata = bool(json_ld_list or og_tags or twitter_tags)

        return {
            "has_structured_metadata": has_metadata,
            "json_ld_schemas_found": len(json_ld_list),
            "json_ld": json_ld_list,
            "open_graph": og_tags,
            "twitter_card": twitter_tags
        }