from typing import Any, Dict, List
from bs4 import BeautifulSoup, Tag


class SelectorGeneratorService:
    """Generates optimal, robust CSS selectors for target HTML elements."""

    @staticmethod
    def generate_css_selector(element: Tag) -> str:
        if not element or element.name == "[document]":
            return ""

        # 1. Prefer unique ID if present and valid
        elem_id = element.get("id")
        if elem_id and isinstance(elem_id, str) and not any(char.isdigit() for char in elem_id[:3]):
            return f"#{elem_id}"

        # 2. Build tag path with class names or nth-of-type fallbacks
        path: List[str] = []
        current: Tag = element

        while current and current.name != "[document]":
            tag_name = current.name
            classes = current.get("class", [])

            if classes and isinstance(classes, list):
                # Filter out utility or dynamically generated class names if needed
                valid_classes = [c for c in classes if not c.startswith("js-") and len(c) < 30]
                if valid_classes:
                    tag_selector = f"{tag_name}.{'.'.join(valid_classes)}"
                    path.insert(0, tag_selector)
                    current = current.parent
                    continue

            # Fallback to nth-of-type indexing if no classes present
            siblings = [s for s in current.parent.find_all(tag_name, recursive=False)] if current.parent else []
            if len(siblings) > 1:
                index = siblings.index(current) + 1
                path.insert(0, f"{tag_name}:nth-of-type({index})")
            else:
                path.insert(0, tag_name)

            current = current.parent

            # Limit path depth to keep selectors readable and maintainable
            if len(path) >= 4:
                break

        return " > ".join(path)

    @classmethod
    def analyze_element_selection(cls, html_content: str, target_text: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html_content, "lxml")
        matched_elements = soup.find_all(string=lambda t: t and target_text.strip() in t.strip())

        results: List[Dict[str, str]] = []
        for match in matched_elements[:5]:
            parent = match.parent
            if parent and isinstance(parent, Tag):
                selector = cls.generate_css_selector(parent)
                results.append({
                    "tag": parent.name,
                    "text_sample": parent.get_text(strip=True)[:60],
                    "generated_css": selector
                })

        return {
            "query": target_text,
            "matches_found": len(results),
            "suggestions": results
        }