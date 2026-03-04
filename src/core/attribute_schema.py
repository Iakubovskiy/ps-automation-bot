"""Attribute schema types and Pydantic validation.

Defines the SourceType enum and a Pydantic model for validating
Category.attribute_schema JSON entries.
"""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, field_validator


class SourceType(str, Enum):
    """How a field's value is obtained."""

    MANUAL = "MANUAL"
    STATIC_DB = "STATIC_DB"
    AI = "AI"


class DataType(str, Enum):
    """Supported data types for validation."""

    STR = "str"
    INT = "int"
    FLOAT = "float"


class AttributeFieldSchema(BaseModel):
    """Pydantic model validating a single field in attribute_schema.

    Example:
        {
            "key": "blade_name",
            "label": "Назва ножа",
            "data_type": "str",
            "source_type": "STATIC_DB",
            "source_ref": "Blade Names",
            "auto_fill_from_value": true
        }

    When auto_fill_from_value is true and user selects an item,
    all fields from the item's value JSON are merged into collected data.
    Subsequent schema fields matching those keys are auto-skipped.
    """

    key: str
    label: str
    data_type: DataType = DataType.STR
    source_type: SourceType = SourceType.MANUAL
    source_ref: Optional[str] = None
    multi_select: bool = False
    auto_fill_from_value: bool = False

    @field_validator("source_ref")
    @classmethod
    def source_ref_required_for_static_db(cls, v, info):
        """Ensure source_ref is set when source_type is STATIC_DB."""
        source_type = info.data.get("source_type")
        if source_type == SourceType.STATIC_DB and not v:
            raise ValueError("source_ref is required when source_type is STATIC_DB")
        return v


def validate_attribute_schema(schema: list[dict]) -> list[AttributeFieldSchema]:
    """Validate a full attribute_schema list, raising on invalid entries."""
    return [AttributeFieldSchema(**field) for field in schema]
