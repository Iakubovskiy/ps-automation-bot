"""GeminiService — wrapper around Google Gemini for AI content generation.

Accepts the Category's system_prompt, collected product attributes,
and product photos. Returns a dict with AI-generated field values.

The system_prompt already defines which fields the AI should produce.
"""
import json
import logging
import os
import tempfile
from typing import Any

from asgiref.sync import sync_to_async
from django.conf import settings as django_settings
from google import genai

from modules.catalog.infrastructure.s3_service import S3Service
from modules.users.domain.organization import Organization

logger = logging.getLogger(__name__)

# Maximum number of photos to send to Gemini (to control token usage)
MAX_PHOTOS_FOR_AI = 2


class GeminiService:
    """Thin wrapper around Google Gemini generative AI."""

    def __init__(self):
        api_key = getattr(django_settings, "GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
        self.client = genai.Client(api_key=api_key)
        self.model_name = getattr(django_settings, "GEMINI_MODEL", "gemini-3-flash-preview")

    async def generate_content(
        self,
        system_prompt: str,
        collected_attributes: dict[str, Any],
        photo_paths: list[str] | None = None,
    ) -> dict[str, Any]:
        """Call Gemini with the category prompt + product data + photos.

        Args:
            system_prompt: Full AI instruction from Category.system_prompt.
            collected_attributes: Product attributes already collected (MANUAL + STATIC_DB).
            photo_paths: Local file paths for product photos (max MAX_PHOTOS_FOR_AI).

        Returns:
            Dict of AI-generated field values (keys defined by system_prompt).
        """
        parts: list = [
            system_prompt,
            f"\nProduct specs:\n```json\n{json.dumps(collected_attributes, ensure_ascii=False, indent=2)}\n```",
        ]

        # Attach product photos (limit to MAX_PHOTOS_FOR_AI)
        uploaded_files = []
        if photo_paths:
            for path in photo_paths[:MAX_PHOTOS_FOR_AI]:
                try:
                    uploaded = self.client.files.upload(file=path)
                    parts.append(uploaded)
                    uploaded_files.append(uploaded)
                except Exception:
                    logger.warning("Failed to upload photo to Gemini: %s", path, exc_info=True)

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=parts,
            )
            return self._parse_response(response.text)
        finally:
            # Clean up uploaded files from Gemini
            for f in uploaded_files:
                try:
                    self.client.files.delete(name=f.name)
                except Exception:
                    pass

    @staticmethod
    def _parse_response(text: str) -> dict[str, Any]:
        """Extract a JSON object from Gemini's response text."""
        cleaned = text.strip()

        # Strip markdown code fences if present
        if cleaned.startswith("```json"):
            cleaned = cleaned.split("\n", 1)[1]
        elif cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]

        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]

        try:
            return json.loads(cleaned.strip())
        except json.JSONDecodeError:
            logger.error("Failed to parse Gemini response as JSON: %s", text[:500])
            return {}


async def download_photos_for_ai(
    s3_paths: list[str],
    organization_id: str,
) -> list[str]:
    """Download product photos from S3 to local temp files for Gemini upload.

    Returns a list of local file paths. Caller is responsible for cleanup.
    """
    if not s3_paths:
        return []

    org = await Organization.objects.aget(id=organization_id)
    s3_service = S3Service(org=org)

    temp_dir = tempfile.mkdtemp(prefix="ai_photos_")
    local_paths: list[str] = []

    for s3_path in s3_paths[:MAX_PHOTOS_FOR_AI]:
        if not s3_path:
            continue
        file_name = os.path.basename(s3_path)
        local_path = os.path.join(temp_dir, file_name)
        try:
            await sync_to_async(s3_service.download_file)(s3_path, local_path)
            local_paths.append(local_path)
        except Exception:
            logger.warning("Failed to download photo from S3: %s", s3_path, exc_info=True)

    return local_paths
