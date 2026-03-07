from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from core.attribute_schema import DataType
from modules.interface.bot_interface.states import DynamicCollectorState
from ..logic.get_next_attribute import ask_next_attribute

router = Router()

@router.message(DynamicCollectorState.attribute_step)
async def process_manual_input(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    field = data["schema"][data["attr_index"]]
    raw, data_type = message.text.strip(), field.get("data_type", DataType.STR)

    try:
        if data_type == DataType.INT: value = int(raw)
        elif data_type == DataType.FLOAT: value = float(raw.replace(",", "."))
        else: value = raw
    except ValueError:
        await message.answer(f"❌ Невірний формат. Очікується {data_type}.")
        return

    collected = data.get("collected", {})
    collected[field["key"]] = value
    await state.update_data(collected=collected, attr_index=data["attr_index"] + 1)
    await message.answer(f"✅ {field.get('label', field['key'])}: {value}")
    await ask_next_attribute(message, state)
