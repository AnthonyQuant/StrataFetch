from enum import Enum
from typing import Any, List, Optional, Union
from pydantic import BaseModel, Field


class DataTypeEnum(str, Enum):
    STRING = "string"
    DECIMAL = "decimal"
    FLOAT = "float"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    URL = "url"


class RuleTypeEnum(str, Enum):
    CSS_SELECTOR = "css_selector"
    XPATH = "xpath"
    LINK_ATTRIBUTE = "link_attribute"
    META_TAG = "meta_tag"


class FieldExtractionRule(BaseModel):
    field_name: str = Field(..., description="Target field key (e.g., 'price', 'product_name')")
    rule_type: Union[RuleTypeEnum, str] = Field(RuleTypeEnum.CSS_SELECTOR, description="Extraction selector type")
    expression: str = Field(..., description="CSS selector or XPath query expression")
    data_type: DataTypeEnum = Field(DataTypeEnum.STRING, description="Target output data type")
    required: bool = Field(False, description="Whether missing field flags a schema validation failure")
    attribute: Optional[str] = Field(None, description="HTML attribute to target (e.g., 'href', 'src')")
    default_value: Optional[Any] = Field(None, description="Fallback value if element is absent")


class ExtractionProfile(BaseModel):
    name: str = Field(..., description="Profile title (e.g., 'E-commerce Product Schema')")
    target_domain: Optional[str] = Field(None, description="Target website domain boundary")
    target_url: Optional[str] = Field(None, description="Default target URL for this profile")
    description: Optional[str] = Field(None, description="Profile scope or description")
    container_selector: Optional[str] = Field(None, description="CSS selector for repeating item card wrappers")
    fields: List[FieldExtractionRule] = Field(default_factory=list, description="List of field extraction rules")
    created_at: Optional[str] = Field(None, description="ISO timestamp of profile creation")
    updated_at: Optional[str] = Field(None, description="ISO timestamp of last update")

    @property
    def field_rules(self) -> List[FieldExtractionRule]:
        """Alias for compatibility across services referencing field_rules."""
        return self.fields


class ExtractionProfileCreate(BaseModel):
    name: str = Field(..., description="Profile title (e.g., 'E-commerce Product Schema')")
    target_domain: Optional[str] = Field(None, description="Target website domain boundary")
    target_url: Optional[str] = Field(None, description="Default target URL for this profile")
    description: Optional[str] = Field(None, description="Profile scope or description")
    container_selector: Optional[str] = Field(None, description="CSS selector for repeating item card wrappers")
    fields: List[FieldExtractionRule] = Field(default_factory=list, description="List of field extraction rules")


class ExtractionProfileResponse(ExtractionProfileCreate):
    id: str = Field(..., description="Unique profile identifier")
    created_at: str
    updated_at: str