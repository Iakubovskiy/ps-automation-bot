"""Rozetka description sanitizer.

Strips URLs, emails, phones, emoji, and forbidden commercial phrases
from product descriptions per Rozetka marketplace rules.
"""
import logging
import re

from modules.distribution.infrastructure.integrations.rozetka.sanitization.rozetka_sanitize_patterns import (
    RE_URL,
    RE_EMAIL,
    RE_PHONE,
    RE_EMOJI,
    RE_STOP_PHRASES,
)

logger = logging.getLogger(__name__)


class DescriptionSanitizer:
    """Cleans product descriptions for Rozetka compliance."""

    @staticmethod
    def sanitize(text: str, offer_id: str) -> str:
        """Remove forbidden content from description text."""
        original = text

        text = RE_URL.sub("", text)
        text = RE_EMAIL.sub("", text)
        text = RE_PHONE.sub("", text)
        text = RE_EMOJI.sub("", text)
        text = RE_STOP_PHRASES.sub("", text)

        # Collapse excessive newlines and spaces
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]{2,}", " ", text)
        text = text.strip()

        if text != original:
            logger.debug("Rozetka offer %s: description was sanitized", offer_id)

        return text
