from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from modules.interface.bot_interface.states import DynamicCollectorState
from ..logic.get_next_attribute import ask_next_attribute

router = Router()

@router.callback_query(DynamicCollectorState.attribute_step, F.data.startswith("bool_"))
async def process_boolean(callback: types.CallbackQuery, state: FSMContext) -> None:
    value = callback.data == "bool_yes"
    data = await state.get_data()
    field = data["schema"][data["attr_index"]]

    collected = data.get("collected", {})
    collected[field["key"]] = value
    await state.update_data(collected=collected, attr_index=data["attr_index"] + 1)

    await callback.answer()
    await callback.message.answer(f"{field.get('label', field['key'])}: {'✅ Так' if value else '❌ Ні'}")
    await ask_next_attribute(callback.message, state)
