"""Test Хорошоп integration directly with mock PublishProductData."""
import asyncio
import logging

from src.dto.gemini_content_dto import GeminiContentDto
from src.dto.input_product_data import InputProductData
from src.dto.publish_product_data import PublishProductData
from src.services.horoshop_integration import HoroshopIntegration

logging.basicConfig(level=logging.INFO)


async def main():
    data = PublishProductData(
        input_data=InputProductData(
            product_code="test-yarchuk-001",
            blade_name="Ярчук",
            total_length=280,
            blade_length=150,
            blade_width=35,
            blade_weight=180,
            blade_thickness=4,
            hardness=58,
            sharpening_angle=20,
            configuration_type=None,
            blade_type="Фултанг",
            sheath_type="Чорні",
            attachments=["Моллі-Лок"],
            has_honing_rod=True,
            has_lanyard=False,
            has_flint=True,
            engraving_count=2,
            handle_material="Мікарта",
            steel="Х12МФ",
            price=1200.0,
            photos=['/app/media/puluj.jpg', '/app/media/puluj-copy.jpg'],
            video_path="",
            video_url="",
        ),
        ai_content=GeminiContentDto(
            title_ua="Ніж Козак",
            title_en="Kozak Knife",
            description_ua="Красивий ніж ручної роботи зі сталі D2.",
            description_en="Beautiful D2 steel knife.",
            meta_keywords_ua="ніж, D2, ручна робота",
            meta_keywords_en="knife, D2, handmade",
            meta_description_ua="Преміальний ніж Козак від Проста Сталь.",
            meta_description_en="Super premium knife",
        ),
    )

    integration = HoroshopIntegration()
    try:
        await integration.publish_product(data)
    except Exception as e:
        logging.error("Failed: %s", e)
    finally:
        await integration.close()


if __name__ == "__main__":
    asyncio.run(main())
