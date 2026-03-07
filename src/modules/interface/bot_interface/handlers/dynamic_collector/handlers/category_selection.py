from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from modules.catalog.infrastructure.category_repository import CategoryRepository
from modules.interface.bot_interface.states import DynamicCollectorState
from ..logic.get_next_attribute import ask_next_attribute

router = Router()


@router.callback_query(DynamicCollectorState.category_select, F.data.startswith("cat_"))
async def process_category(callback: types.CallbackQuery, state: FSMContext) -> None:
    category_id = int(callback.data.replace("cat_", ""))
    category = await CategoryRepository.afind_by_id(category_id)

    if not category:
        await callback.answer("Категорію не знайдено!", show_alert=True)
        return

    raw_schema = await category.aget_attribute_schema()
    await state.update_data(category_id=category_id, category_name=category.name, schema=raw_schema, attr_index=0,
                            collected={})

    await callback.answer()
    await callback.message.answer(f"Обрано: {category.name}")
    await ask_next_attribute(callback.message, state)
