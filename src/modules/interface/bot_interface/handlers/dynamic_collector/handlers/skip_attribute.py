from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from ..logic.get_next_attribute import ask_next_attribute

router = Router()

@router.callback_query(F.data == "skip_attr")
async def skip_attr(callback: types.CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    field = data["schema"][data["attr_index"]]
    await state.update_data(attr_index=data["attr_index"] + 1)
    await callback.answer()
    await callback.message.answer(f"⏩ {field.get('label', field['key'])} — пропущено")
    await ask_next_attribute(callback.message, state)
