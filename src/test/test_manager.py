"""Smoke test for ProductManager with real GeminiService."""
import asyncio
import logging

from src.dto.input_product_data import InputProductData
from src.services.gemini_service import GeminiService
from src.services.product_manager import ProductManager

logging.basicConfig(level=logging.INFO)


async def main():
    mock_input = InputProductData(
        product_code= 'puluj-black-vegvizir-clip',
        blade_name="Пулюй",
        total_length=280,
        blade_length=150,
        blade_width=35,
        blade_weight=180,
        blade_thickness=4.5,
        hardness=58,
        sharpening_angle=40,
        configuration_type=None,
        blade_type="Ніж скелетник",
        sheath_type="Піхви скелетник",
        attachments=["Моллі-Лок"],
        has_honing_rod=True,
        has_lanyard=True,
        has_flint=False,
        engraving_count=3,
        handle_material="Паракорд",
        steel="Х12МФ",
        price=3500.0,
        photos=["/app/media/puluj.jpg"],
        video_path="",
        video_url="",
    )

    manager = ProductManager(ai_service=GeminiService())

    try:
        await manager.process(mock_input)
    except NotImplementedError as e:
        print(f"\n✅ Pipeline works! Stopped at publish stub: {e}")


if __name__ == "__main__":
    asyncio.run(main())
