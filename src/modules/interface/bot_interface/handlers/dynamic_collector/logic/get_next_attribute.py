from aiogram import types
from aiogram.fsm.context import FSMContext
from core.attribute_schema import SourceType, DataType
from modules.catalog.infrastructure.static_reference_repository import StaticReferenceRepository
from modules.interface.bot_interface.states import DynamicCollectorState
from .finalize_creation import finalize_creation
from modules.interface.bot_interface.keyboards.keyboards import (
    get_static_ref_keyboard, get_multi_select_ref_keyboard,
    get_boolean_keyboard, get_boolean_keyboard_with_skip,
    get_finish_files_keyboard, get_skip_keyboard
)


async def ask_next_attribute(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    schema, index, collected = data["schema"], data["attr_index"], data.get("collected", {})

    while index < len(schema):
        field = schema[index]
        if field.get("source_type") == SourceType.AI or field["key"] in collected:
            index += 1
            continue
        break

    if index >= len(schema):
        await state.update_data(attr_index=index)
        await message.answer(
            "🚀 Запускаю обробку товару..."
        )
        await finalize_creation(message, state)
        await message.answer(
            "✅ Товар успішно оброблено!"
        )
        return

    await state.update_data(attr_index=index)
    field = schema[index]
    label, source_type = field.get("label", field["key"]), field.get("source_type", SourceType.MANUAL)
    data_type, multi_select, optional = field.get("data_type", DataType.STR), field.get("multi_select",
                                                                                        False), field.get("optional",
                                                                                                          False)

    if source_type == SourceType.STATIC_DB:
        await state.set_state(DynamicCollectorState.attribute_step)
        refs = await StaticReferenceRepository.afind_by_group(data.get("organization_id"), field.get("source_ref", ""))
        if not refs:
            await message.answer(f"Введіть {label}:")
            return

        ref_list = [{"key": r.key, "label": r.label} for r in refs]
        if multi_select:
            await state.update_data(multi_selected=[])
            kb = get_multi_select_ref_keyboard(ref_list)
            if optional: kb.inline_keyboard.append(
                [types.InlineKeyboardButton(text="⏩ Пропустити", callback_data="skip_attr")])
            await message.answer(f"Оберіть {label} (декілька):", reply_markup=kb)
        else:
            kb = get_static_ref_keyboard(ref_list)
            if optional: kb.inline_keyboard.append(
                [types.InlineKeyboardButton(text="⏩ Пропустити", callback_data="skip_attr")])
            await message.answer(f"Оберіть {label}:", reply_markup=kb)
        return

    if data_type == DataType.BOOLEAN:
        await state.set_state(DynamicCollectorState.attribute_step)
        kb = get_boolean_keyboard_with_skip() if optional else get_boolean_keyboard()
        await message.answer(f"Чи є {label}?", reply_markup=kb)
        return

    if data_type in [DataType.FILE, DataType.FILE_ARRAY]:
        await state.set_state(DynamicCollectorState.file_upload)
        msg = f"📎 Надішліть файл(и) для «{label}»:"
        kb = get_finish_files_keyboard() if data_type == DataType.FILE_ARRAY else (
            get_skip_keyboard("skip_attr") if optional else None)
        await message.answer(msg, reply_markup=kb)
        return

    await state.set_state(DynamicCollectorState.attribute_step)
    await message.answer(f"Введіть {label}:", reply_markup=get_skip_keyboard("skip_attr") if optional else None)