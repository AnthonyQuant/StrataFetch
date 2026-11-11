from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup
from lxml import etree
from app.models.extraction_profile import FieldExtractionRule, RuleTypeEnum


class ParserRuleService:
    """Evaluates extraction profile rules against raw HTML content."""

    @staticmethod
    def extract_field_value(soup: Any, tree: Optional[etree._Element], rule: FieldExtractionRule) -> Optional[Any]:
        raw_val: Optional[Any] = None

        # Normalize rule_type string/enum representation
        rule_type_val = rule.rule_type.value if hasattr(rule.rule_type, "value") else str(rule.rule_type)

        if rule_type_val in (RuleTypeEnum.CSS_SELECTOR.value, "css_selector"):
            if hasattr(soup, "select_one"):
                element = soup.select_one(rule.expression)
                if element:
                    if rule.attribute:
                        raw_val = element.get(rule.attribute)
                    else:
                        raw_val = element.get_text(strip=True)

        elif rule_type_val in (RuleTypeEnum.XPATH.value, "xpath"):
            if tree is not None:
                try:
                    results = tree.xpath(rule.expression)
                    if results:
                        res = results[0]
                        if isinstance(res, etree._Element):
                            if rule.attribute:
                                raw_val = res.get(rule.attribute)
                            else:
                                raw_val = "".join(res.itertext()).strip()
                        else:
                            raw_val = str(res).strip()
                except Exception:
                    raw_val = None

        elif rule_type_val in (RuleTypeEnum.META_TAG.value, "meta_tag"):
            if hasattr(soup, "find"):
                meta = soup.find("meta", attrs={"name": rule.expression}) or soup.find("meta", attrs={"property": rule.expression})
                if meta:
                    raw_val = meta.get("content")

        elif rule_type_val in (RuleTypeEnum.LINK_ATTRIBUTE.value, "link_attribute"):
            if hasattr(soup, "select_one"):
                element = soup.select_one(rule.expression)
                if element:
                    raw_val = element.get(rule.attribute or "href")

        if raw_val is None and hasattr(rule, "default_value"):
            raw_val = rule.default_value

        return raw_val

    @classmethod
    def apply_profile_rules(
        cls,
        html_content: str,
        rules: List[FieldExtractionRule]
    ) -> Dict[str, Any]:
        soup = BeautifulSoup(html_content, "lxml")
        try:
            tree = etree.HTML(html_content)
        except Exception:
            tree = None

        extracted_data: Dict[str, Any] = {}
        for rule in rules:
            extracted_data[rule.field_name] = cls.extract_field_value(soup, tree, rule)

        return extracted_data