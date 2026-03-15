"""Rozetka product name sanitizer and template builder.

Handles name validation rules:
- Remove forbidden punctuation (quotes, brackets)
- Ensure vendor is present in the name
- Build names from configurable templates with field/param placeholders
"""
import logging
import re

from modules.distribution.infrastructure.integrations.rozetka.sanitization.rozetka_sanitize_patterns import (
    RE_NAME_FORBIDDEN,
    RE_TEMPLATE_PLACEHOLDER,
)

logger = logging.getLogger(__name__)


class NameSanitizer:
    """Sanitizes and builds product names for Rozetka."""

    @staticmethod
    def sanitize(name: str, vendor: str) -> str:
        """Remove forbidden punctuation and ensure vendor is in the name."""
        name = RE_NAME_FORBIDDEN.sub("", name)
        name = re.sub(r"\s{2,}", " ", name).strip()

        if vendor and vendor.lower() not in name.lower():
            parts = name.split(" ", 1)
            if len(parts) == 2:
                name = f"{parts[0]} {vendor} {parts[1]}"
            else:
                name = f"{name} {vendor}"

        return name

    @staticmethod
    def build_from_template(
        template: str,
        field_mappings: dict,
        param_mappings: list[tuple],
        offer_id: str,
    ) -> str | None:
        """Build a product name from a template string.

        Template format: "{name} {vendor} {param:Довжина клинка} мм {article}"

        Placeholders:
            {field_name}        -- value from field_mappings
            {param:Param Name}  -- value from param_mappings by name

        Returns None if no placeholders could be resolved.
        """
        param_lookup = {name: value for name, value in param_mappings}
        resolved_any = False

        def _replace(match: re.Match) -> str:
            nonlocal resolved_any
            key = match.group(1)

            if key.startswith("param:"):
                param_name = key[6:]
                value = param_lookup.get(param_name)
                if value is not None:
                    resolved_any = True
                    if isinstance(value, list):
                        return ", ".join(str(v) for v in value)
                    return str(value)
                return ""

            value = field_mappings.get(key, "")
            if value and str(value).strip():
                resolved_any = True
                if isinstance(value, list):
                    return ", ".join(str(v) for v in value)
                return str(value)
            return ""

        result = RE_TEMPLATE_PLACEHOLDER.sub(_replace, template)

        if not resolved_any:
            logger.warning(
                "Rozetka offer %s: name template resolved no values",
                offer_id,
            )
            return None

        # Collapse multiple spaces and strip trailing separators
        result = re.sub(r"\s{2,}", " ", result)
        result = re.sub(r"[\s\-]+$", "", result)
        result = result.strip()
        return result or None
