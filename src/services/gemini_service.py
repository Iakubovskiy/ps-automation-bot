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

- title_ua           — use product name from specs, colors, engraving style/pictures. 
You should also use one of style you consider appropriate [tactical, survival, fighting, combat, bushcraft, edc] but only one, and go with this concept further. 
Example (Ніж для виживання «Тигролов» | «Stalker» Гравіювання Череп у протигазі)
- title_en           — translation to English title_ua 
- description_ua     — it should consist of 3 blocks. The first one is short description, you should mention knife name that is provided, 
describe it's design and mention custom engraving at the end. 
Example (Ніж для виживання «Тигролов» у версії «Stalker» створений для екстремальних умов. Клинок зі сталі Х12МФ має захисне покриття травлення (Stonewash). Чорне руків'я з мікарти з 3D обробкою гарантує надійний хват. Дизайн просякнутий духом Зони: на клинку вигравіювано символ Biohazard та череп у протигазі, а на піхвах — напис Hard to Kill. Комплект оснащений зручним вільним підвісом та яскравим червоним темляком з намистиною. Ми також пропонуємо нанести індивідуальне гравіювання вашого позивного або гасла замість базового малюнка.)
The second block is set components, thus based on what is in the specs (it's high priority) and what is in the photos attached you should write this block.
Example (
Комплектація
- Ніж для виживання «Тигролов»: покриття травлення руків'я з мікарти колір Чорний
- Гравіювання на клинку: символ Череп у протигазі
- Піхви з ABS пластику: колір Чорний
- Гравіювання на піхвах: напис
- Кріплення: Вільний підвіс
- Темляк
)
And the block 3 is bigger SEO oriented description, thus based on the chosen topic in title you should find and add keyword.  It should have 2-3 paragraphs with 2-3 sentences in each. Don't separate these paragraphs with enter
Example
(«Stalker» — виживає підготовлений.
Модель «Тигролов» — це ідеальний супутник для довгих рейдів. Хижа геометрія клинка з легким вигином (recurve) забезпечує агресивний різ та чудові січні властивості. Ніж виготовлений з інструментальної сталі Х12МФ, яка довго тримає заточку навіть при роботі з твердими матеріалами. Покриття Stonewash додає металу брутальності та маскує подряпини.
Естетика комплекту побудована навколо теми техногенної катастрофи та виживання. Чорне руків'я з мікарти не боїться вологи та бруду. Гравіювання Biohazard та Череп у респіраторі попереджають про небезпеку, а напис «Hard to Kill» («Важко вбити») на піхвах підкреслює живучість власника.
Для максимального комфорту при носінні ніж комплектується системою вільний підвіс. Це дозволяє ножу вільно рухатися разом з тілом, не заважаючи сидіти в транспорті або долати перешкоди. Яскравий акцент — плетений темляк із бронзовою намистиною, що допомагає швидко вийняти ніж.
)
At the result take all 3 blocks and make one product description. IMPORTANT you mustn't highlight these blocks, just make enters after them   
- description_en     — translate description_ua to English
- meta_keywords_ua   — comma-separated SEO keywords, approximately 10 words in ukrainian
- meta_keywords_en   — comma-separated SEO keywords, approximately 10 words in English
- meta_description_ua — a SEO meta description (≤160 chars) in ukrainian and using emoji. Example (☢️ Ніж для виживання «Тигролов» Stalker. 💀 Вільний підвіс, чорна мікарта. Гравіювання Biohazard та Череп. Напис Hard to Kill. Темляк. Індивідуальне гравіювання.)
- meta_description_en — a SEO meta description (≤160 chars) in English and using emoji Example (☢️ Survival Knife "Tygrolov" Stalker. 💀 Free suspension, black Micarta. Biohazard and Skull engraving. Hard to Kill inscription. Lanyard. Custom engraving.)
- engraving_style – choose one style from the list [Скандинавські символи / руни, Аніме, 
Емблеми батальйонів, Патріотичні, Герби / історичні символи, Черепи / темна естетика, Із кінофільмів,
Ігри, Авторські дизайни, Індивідуальні написи] 
You are allowed to choose more then 1 but not more then 3 style 

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
            photo_paths = photo_paths[:2]
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
