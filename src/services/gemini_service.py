"""Service for generating product content using Google Gemini AI.

The AI receives product specs from Google Sheets plus product photos
and generates: product_code, title, description, meta_keywords,
meta_description, etsy_title, etsy_description, etsy_tags.

Output is bilingual — Ukrainian and English.
"""
import json
import os
from dataclasses import fields

from google import genai

from src.dto.gemini_content_dto import GeminiContentDto
from src.services.ai_service import AiService

MOCK_PROMPT = """\
You are an expert product copywriter for a Ukrainian knife-making brand.
You will receive:
  1. A JSON object with the knife's technical specs.
  2. One or more product photos.

Generate the following fields in **both Ukrainian and English**
(use the format "UA: … / EN: …" for each field):

- product_code   — a short unique product code (e.g. "PS-D2-001")
- title           — an appealing product title
- description     — a rich marketing description (2-3 paragraphs)
- meta_keywords   — comma-separated SEO keywords
- meta_description— a single-sentence SEO meta description (≤160 chars)
- etsy_title      — an Etsy-optimised listing title (≤140 chars)
- etsy_description— a detailed Etsy listing description
- etsy_tags       — up to 13 comma-separated Etsy tags
- engraving_description — carefully examine the product photos and describe
  the engraving style visible on the blade: what patterns, motifs, or images
  are engraved, the technique used (e.g. acid etching, hand engraving,
  laser engraving), and the overall artistic style. If no engraving is
  visible, state that the blade has no engraving.

Return your answer as a JSON object with exactly these keys.
"""


class GeminiService(AiService):
    """Wrapper around Google Gemini generative AI."""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-3-flash-preview"

    async def generate_content(
            self,
            specs: dict,
            photo_paths: list[str] | None = None,
    ) -> GeminiContentDto:
        """Call Gemini with product specs + photos and return AI fields."""
        parts: list = [
            MOCK_PROMPT,
            f"\nProduct specs:\n```json\n{json.dumps(specs, ensure_ascii=False, indent=2)}\n```",
        ]

        if photo_paths:
            for path in photo_paths:
                uploaded = self.client.files.upload(file=path)
                parts.append(uploaded)

        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=parts
        )

        return self._parse_response(response.text)

    @staticmethod
    def _parse_response(text: str) -> GeminiContentDto:
        """Extract the JSON object from the model's response text."""
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned.split("\n", 1)[1]
        elif cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]

        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            data = {}

        dto_fields = {f.name for f in fields(GeminiContentDto)}
        return GeminiContentDto(**{key: data.get(key, "") for key in dto_fields})
