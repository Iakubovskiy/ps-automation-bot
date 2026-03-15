"""Rozetka vendor name sanitizer.

Cleans vendor names per Rozetka marketplace rules:
- Strip legal form prefixes (ТМ, ТОВ, ФОП, ЛТД, торгова марка)
- Convert ALL CAPS to Title Case (except short abbreviations)
"""
import re


class VendorSanitizer:
    """Cleans vendor names for Rozetka compliance."""

    # Matches Ukrainian legal form prefixes to strip from vendor names
    _RE_LEGAL_FORMS = re.compile(
        r"\b(?:торгова марка|ТМ|ЛТД|ТОВ|ФОП)\b\.?\s*",
        re.IGNORECASE,
    )

    @staticmethod
    def clean(vendor: str) -> str:
        """Clean vendor name per Rozetka rules."""
        vendor = VendorSanitizer._RE_LEGAL_FORMS.sub("", vendor).strip()

        if len(vendor) > 3 and vendor == vendor.upper():
            vendor = vendor.title()

        return vendor
