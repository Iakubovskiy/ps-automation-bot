"""Abstract interface for AI content generation services."""
from abc import ABC, abstractmethod

from src.dto.gemini_content_dto import GeminiContentDto


class AiService(ABC):
    """Interface for AI-powered product content generation.

    Implement this to swap the underlying AI provider
    (e.g. Gemini, OpenAI, Claude).
    """

    @abstractmethod
    async def generate_content(
        self,
        specs: dict,
        photo_paths: list[str],
    ) -> GeminiContentDto:
        """Generate marketing content from product specs and photos.

        Args:
            specs: Product specification dict.
            photo_paths: Paths/URLs to product photos.

        Returns:
            A ``GeminiContentDto`` with the generated content.
        """
