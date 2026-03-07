import logging
from aiogram import types
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
from modules.catalog.application.product.create.create_product_use_case import CreateProductUseCase
from modules.catalog.application.product.create.dto.create_product_dto import CreateProductDto

logger = logging.getLogger(__name__)

async def finalize_creation(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    await message.answer("⏳ Створюю продукт…")

    dto = CreateProductDto(
        organization_id=data.get("organization_id", ""),
        category_id=data["category_id"],
        attributes=data.get("collected", {}),
        photo_paths=data.get("photos", []),
        video_path=data.get("video_path", ""),
        video_url=data.get("youtube_link", ""),
    )

    try:
        use_case = CreateProductUseCase()
        product = await sync_to_async(use_case.execute)(dto)
        await message.answer(f"✅ Продукт <b>{data.get('category_name', '')}</b> створено!\nID: <code>{product.id}</code>")
    except Exception:
        logger.exception("Product creation failed")
        await message.answer("❌ Помилка при створенні.")
    finally:
        await state.clear()