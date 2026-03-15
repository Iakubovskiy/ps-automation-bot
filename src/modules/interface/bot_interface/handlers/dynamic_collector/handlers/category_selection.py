from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from modules.catalog.infrastructure.product_schema_repository import ProductSchemaRepository
from modules.interface.bot_interface.states import DynamicCollectorState
from ..logic.get_next_attribute import ask_next_attribute

router = Router()


@router.callback_query(DynamicCollectorState.category_select, F.data.startswith("cat_"))
async def process_category(callback: types.CallbackQuery, state: FSMContext) -> None:
    schema_id = int(callback.data.replace("cat_", ""))
    schema = await ProductSchemaRepository.afind_by_id(schema_id)

    if not schema:
        await callback.answer("Категорію не знайдено!", show_alert=True)
        return

    raw_schema = await schema.aget_attribute_schema()
    await state.update_data(product_schema_id=schema_id, category_name=schema.name, schema=raw_schema, attr_index=0,
                            collected={})

    await callback.answer()
    await callback.message.answer(f"Обрано: {schema.name}")
    await ask_next_attribute(callback.message, state)
