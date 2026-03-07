from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from modules.catalog.infrastructure.static_reference_repository import StaticReferenceRepository
from modules.interface.bot_interface.states import DynamicCollectorState
from modules.interface.bot_interface.keyboards.keyboards import get_multi_select_ref_keyboard
from ..logic.get_next_attribute import ask_next_attribute

router = Router()


@router.callback_query(DynamicCollectorState.attribute_step, F.data.startswith("ref_"))
async def process_single_ref(callback: types.CallbackQuery, state: FSMContext) -> None:
    key = callback.data.replace("ref_", "")
    data = await state.get_data()
    field = data["schema"][data["attr_index"]]
    collected = data.get("collected", {})
    collected[field["key"]] = key

    await state.update_data(collected=collected, attr_index=data["attr_index"] + 1)
    await callback.answer()
    await callback.message.answer(f"✅ {field.get('label', field['key'])}: {key}")
    await ask_next_attribute(callback.message, state)


@router.callback_query(DynamicCollectorState.attribute_step, F.data.startswith("mref_"))
async def process_multi_ref(callback: types.CallbackQuery, state: FSMContext) -> None:
    value = callback.data.replace("mref_", "")
    data = await state.get_data()
    index = data["attr_index"]
    field = data["schema"][index]
    selected = data.get("multi_selected", [])

    if value == "done":
        if not selected:
            await callback.answer("Оберіть хоча б один варіант!", show_alert=True)
            return
        collected = data.get("collected", {})
        collected[field["key"]] = selected
        await state.update_data(collected=collected, attr_index=index + 1, multi_selected=[])
        await callback.message.answer(f"✅ {field.get('label', field['key'])}: {', '.join(selected)}")
        await ask_next_attribute(callback.message, state)
    else:
        if value in selected:
            selected.remove(value)
        else:
            selected.append(value)
        await state.update_data(multi_selected=selected)

        refs = await StaticReferenceRepository.afind_by_group(data.get("organization_id"), field.get("source_ref", ""))
        await callback.message.edit_reply_markup(
            reply_markup=get_multi_select_ref_keyboard([{"key": r.key, "label": r.label} for r in refs], set(selected)))
        await callback.answer()
