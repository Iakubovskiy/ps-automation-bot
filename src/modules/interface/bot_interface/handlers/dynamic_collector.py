"""Dynamic product collector — builds bot dialog from Category.attribute_schema.

Replaces the old hardcoded collector.py with a schema-driven FSM flow:
  /start → pick category → iterate attribute_schema fields → photos → video → YouTube → create product

For each attribute field in the schema:
  - source_type == STATIC_DB → query StaticReference by source_ref → inline keyboard
  - source_type == MANUAL → prompt text input, validate by data_type
  - source_type == AI → skip (generated later by AI service)
  - multi_select == True → multi-select keyboard with toggle
"""
import asyncio
import logging
from collections import defaultdict

from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from core.attribute_schema import SourceType, DataType, validate_attribute_schema

from modules.interface.bot_interface.states import DynamicCollectorState
from modules.interface.bot_interface.keyboards import (
    get_category_keyboard,
    get_static_ref_keyboard,
    get_multi_select_ref_keyboard,
    get_finish_photos_keyboard,
    get_video_choice_keyboard,
    get_skip_keyboard,
)

from modules.catalog.infrastructure.category_repository import CategoryRepository
from modules.catalog.infrastructure.static_reference_repository import StaticReferenceRepository
from modules.catalog.application.product.create.create_product_use_case import CreateProductUseCase
from modules.catalog.application.product.create.dto.create_product_dto import CreateProductDto

from services.file_manager import generate_item_uuid, save_file_path

logger = logging.getLogger(__name__)
router = Router()

_photo_locks: dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)
_photo_debounce_tasks: dict[int, asyncio.Task] = {}


# ── /start ───────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext) -> None:
    """Start collection: show available categories."""
    await state.clear()

    categories = CategoryRepository.find_all()
    if not categories:
        await message.answer("⚠️ Немає доступних категорій. Зверніться до адміністратора.")
        return

    cat_list = [{"id": c.id, "name": c.name} for c in categories]

    item_uuid = generate_item_uuid()
    await state.update_data(item_uuid=item_uuid, photos=[], collected={})

    await message.answer(
        "Привіт! Оберіть категорію виробу:",
        reply_markup=get_category_keyboard(cat_list),
    )
    await state.set_state(DynamicCollectorState.category_select)


# ── Category selection ───────────────────────────────────────────────

@router.callback_query(DynamicCollectorState.category_select, F.data.startswith("cat_"))
async def process_category(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Load category schema and begin attribute collection."""
    category_id = int(callback.data.replace("cat_", ""))
    category = CategoryRepository.find_by_id(category_id)

    if not category:
        await callback.answer("Категорію не знайдено!", show_alert=True)
        return

    raw_schema = category.attribute_schema or []

    # Validate and parse schema into typed objects
    try:
        parsed = validate_attribute_schema(raw_schema)
    except Exception as exc:
        logger.exception("Invalid attribute_schema for category %s", category_id)
        await callback.answer(f"Помилка схеми: {exc}", show_alert=True)
        return

    # Store raw dicts for FSM serialization, but we validate upfront
    await state.update_data(
        category_id=category_id,
        category_name=category.name,
        schema=raw_schema,
        attr_index=0,
        collected={},
        multi_selected=[],
    )

    await callback.answer()
    await callback.message.answer(f"Обрано категорію: {category.name}")

    await _ask_next_attribute(callback.message, state)


# ── Dynamic attribute collection ─────────────────────────────────────

async def _ask_next_attribute(message: types.Message, state: FSMContext) -> None:
    """Ask for the next attribute in the schema, or proceed to media if done."""
    data = await state.get_data()
    schema = data["schema"]
    index = data["attr_index"]

    collected = data.get("collected", {})

    # Skip AI fields and fields already auto-filled from a previous selection
    while index < len(schema):
        field = schema[index]
        if field.get("source_type") == SourceType.AI:
            index += 1
            continue
        if field["key"] in collected:
            index += 1
            continue
        break

    if index >= len(schema):
        # All collectible attributes done — move to photos
        await state.update_data(attr_index=index)
        await state.set_state(DynamicCollectorState.media_photos)
        await message.answer(
            "✅ Всі характеристики зібрано!\n\n"
            "Тепер надішліть фото виробу (можна декілька). "
            "Коли закінчите — натисніть кнопку нижче."
        )
        return

    await state.update_data(attr_index=index)
    field = schema[index]
    label = field.get("label", field["key"])
    source_type = field.get("source_type", SourceType.MANUAL)
    multi_select = field.get("multi_select", False)

    await state.set_state(DynamicCollectorState.attribute_step)

    if source_type == SourceType.STATIC_DB:
        # Query StaticReference for options
        source_ref = field.get("source_ref", "")
        org_id = data.get("organization_id", "")
        refs = StaticReferenceRepository.find_by_group(org_id, source_ref)

        if not refs:
            # No references found — fall back to manual input
            await message.answer(f"Введіть {label}:")
            return

        ref_list = [{"key": r.key, "label": r.label} for r in refs]

        if multi_select:
            await state.update_data(multi_selected=[])
            await message.answer(
                f"Оберіть {label} (можна декілька), потім натисніть 'Готово':",
                reply_markup=get_multi_select_ref_keyboard(ref_list),
            )
        else:
            await message.answer(
                f"Оберіть {label}:",
                reply_markup=get_static_ref_keyboard(ref_list),
            )
    else:
        # MANUAL input
        data_type = field.get("data_type", DataType.STR)
        hint = ""
        if data_type == DataType.INT:
            hint = " (ціле число)"
        elif data_type == DataType.FLOAT:
            hint = " (число)"
        await message.answer(f"Введіть {label}{hint}:")


# ── STATIC_DB: single select ────────────────────────────────────────

@router.callback_query(DynamicCollectorState.attribute_step, F.data.startswith("ref_"))
async def process_static_ref(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Handle single-select from StaticReference keyboard."""
    selected_key = callback.data.replace("ref_", "")
    data = await state.get_data()
    schema = data["schema"]
    index = data["attr_index"]
    field = schema[index]

    collected = data.get("collected", {})
    collected[field["key"]] = selected_key

    # Auto-fill: merge item's value JSON into collected data
    auto_fill = field.get("auto_fill_from_value", False)
    if auto_fill:
        source_ref = field.get("source_ref", "")
        org_id = data.get("organization_id", "")
        item = StaticReferenceRepository.find_by_key(org_id, source_ref, selected_key)
        if item and isinstance(item.value, dict):
            collected.update(item.value)
            filled_keys = list(item.value.keys())
            logger.info("Auto-filled %d fields from %s: %s", len(filled_keys), selected_key, filled_keys)

    await state.update_data(
        collected=collected,
        attr_index=index + 1,
    )

    await callback.answer()
    label_text = field.get('label', field['key'])
    msg = f"✅ {label_text}: {selected_key}"
    if auto_fill:
        msg += "\n📋 Характеристики заповнено автоматично."
    await callback.message.answer(msg)
    await _ask_next_attribute(callback.message, state)


# ── STATIC_DB: multi select toggle ──────────────────────────────────

@router.callback_query(DynamicCollectorState.attribute_step, F.data.startswith("mref_"))
async def process_multi_ref(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Toggle a multi-select option or confirm selection."""
    value = callback.data.replace("mref_", "")

    if value == "done":
        # Confirm multi-select
        data = await state.get_data()
        schema = data["schema"]
        index = data["attr_index"]
        field = schema[index]
        selected = data.get("multi_selected", [])

        if not selected:
            await callback.answer("Оберіть хоча б один варіант!", show_alert=True)
            return

        collected = data.get("collected", {})
        collected[field["key"]] = selected
        await state.update_data(
            collected=collected,
            attr_index=index + 1,
            multi_selected=[],
        )

        await callback.answer()
        await callback.message.answer(
            f"✅ {field.get('label', field['key'])}: {', '.join(selected)}"
        )
        await _ask_next_attribute(callback.message, state)
    else:
        # Toggle option
        data = await state.get_data()
        selected: list[str] = data.get("multi_selected", [])
        if value in selected:
            selected.remove(value)
        else:
            selected.append(value)

        await state.update_data(multi_selected=selected)

        # Rebuild keyboard
        schema = data["schema"]
        index = data["attr_index"]
        field = schema[index]
        source_ref = field.get("source_ref", "")
        org_id = data.get("organization_id", "")
        refs = StaticReferenceRepository.find_by_group(org_id, source_ref)
        ref_list = [{"key": r.key, "label": r.label} for r in refs]

        await callback.message.edit_reply_markup(
            reply_markup=get_multi_select_ref_keyboard(ref_list, set(selected)),
        )
        await callback.answer()


# ── MANUAL text input ────────────────────────────────────────────────

@router.message(DynamicCollectorState.attribute_step)
async def process_manual_input(message: types.Message, state: FSMContext) -> None:
    """Handle free-text input for MANUAL fields with type validation."""
    data = await state.get_data()
    schema = data["schema"]
    index = data["attr_index"]
    field = schema[index]

    raw = message.text.strip()
    data_type = field.get("data_type", DataType.STR)

    # Type validation
    try:
        if data_type == DataType.INT:
            value = int(raw)
        elif data_type == DataType.FLOAT:
            value = float(raw.replace(",", "."))
        else:
            value = raw
    except (ValueError, TypeError):
        await message.answer(f"❌ Невірний формат. Очікується {data_type}. Спробуйте ще раз:")
        return

    collected = data.get("collected", {})
    collected[field["key"]] = value
    await state.update_data(
        collected=collected,
        attr_index=index + 1,
    )

    await message.answer(f"✅ {field.get('label', field['key'])}: {value}")
    await _ask_next_attribute(message, state)


# ── Photos ───────────────────────────────────────────────────────────

@router.message(DynamicCollectorState.media_photos, F.photo)
async def process_photos(message: types.Message, state: FSMContext, bot) -> None:
    """Save photos to local storage with debounce."""
    user_id = message.from_user.id
    async with _photo_locks[user_id]:
        data = await state.get_data()
        item_uuid = data["item_uuid"]
        photo_count = len(data.get("photos", [])) + 1

        file_id = message.photo[-1].file_id
        file = await bot.get_file(file_id)

        file_name = f"photo_{photo_count}.jpg"
        dest = save_file_path(item_uuid, file_name)
        await bot.download_file(file.file_path, dest)

        photos = data.get("photos", [])
        photos.append(dest)
        await state.update_data(photos=photos)

        # Debounce: wait for user to finish sending photos
        prev_task = _photo_debounce_tasks.get(user_id)
        if prev_task and not prev_task.done():
            prev_task.cancel()

        _photo_debounce_tasks[user_id] = asyncio.create_task(
            _send_photo_summary(message, state, user_id)
        )


async def _send_photo_summary(
    message: types.Message, state: FSMContext, user_id: int
) -> None:
    """Wait briefly, then send a summary with the finish button."""
    await asyncio.sleep(1.5)

    async with _photo_locks[user_id]:
        data = await state.get_data()
        total = len(data.get("photos", []))

    await message.answer(
        f"📸 Збережено фото: {total} шт. Бажаєте додати ще?",
        reply_markup=get_finish_photos_keyboard(),
    )


@router.callback_query(DynamicCollectorState.media_photos, F.data == "finish_photos")
async def finish_photos(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Photos collected — ask about video."""
    data = await state.get_data()
    count = len(data.get("photos", []))
    await callback.answer()
    await callback.message.answer(f"✅ Збережено фото: {count} шт.")

    await callback.message.answer(
        "Бажаєте завантажити відео?",
        reply_markup=get_video_choice_keyboard(),
    )
    await state.set_state(DynamicCollectorState.media_video)


# ── Video ────────────────────────────────────────────────────────────

@router.callback_query(DynamicCollectorState.media_video, F.data == "upload_video")
async def ask_for_video(callback: types.CallbackQuery, state: FSMContext) -> None:
    """User chose to upload a video."""
    await callback.answer()
    await callback.message.answer("Надішліть відео:")


@router.message(DynamicCollectorState.media_video, F.video)
async def process_video(message: types.Message, state: FSMContext, bot) -> None:
    """Save the uploaded video."""
    data = await state.get_data()
    item_uuid = data["item_uuid"]

    file = await bot.get_file(message.video.file_id)
    ext = file.file_path.rsplit(".", 1)[-1] if "." in file.file_path else "mp4"
    dest = save_file_path(item_uuid, f"video.{ext}")
    await bot.download_file(file.file_path, dest)
    await state.update_data(video_path=dest)

    await message.answer("✅ Відео збережено.")
    await _ask_youtube(message, state)


@router.callback_query(DynamicCollectorState.media_video, F.data == "skip_video")
async def skip_video(callback: types.CallbackQuery, state: FSMContext) -> None:
    """User skipped video upload."""
    await callback.answer()
    await callback.message.answer("Відео пропущено.")
    await _ask_youtube(callback.message, state)


# ── YouTube link ─────────────────────────────────────────────────────

async def _ask_youtube(message: types.Message, state: FSMContext) -> None:
    """Ask for a YouTube link or skip."""
    await message.answer(
        "Введіть посилання на YouTube-відео або натисніть 'Пропустити':",
        reply_markup=get_skip_keyboard("skip_youtube"),
    )
    await state.set_state(DynamicCollectorState.youtube_link)


@router.message(DynamicCollectorState.youtube_link, F.text)
async def process_youtube(message: types.Message, state: FSMContext) -> None:
    """Save YouTube link and finalize."""
    link = message.text.strip()
    if "youtu" not in link:
        await message.answer(
            "Це не схоже на YouTube-посилання. Спробуйте ще раз або натисніть 'Пропустити'."
        )
        return
    await state.update_data(youtube_link=link)
    await message.answer(f"✅ Посилання збережено: {link}")
    await _finalize(message, state)


@router.callback_query(DynamicCollectorState.youtube_link, F.data == "skip_youtube")
async def skip_youtube(callback: types.CallbackQuery, state: FSMContext) -> None:
    """User skipped YouTube link."""
    await callback.answer()
    await callback.message.answer("YouTube пропущено.")
    await _finalize(callback.message, state)


# ── Finalize ─────────────────────────────────────────────────────────

async def _finalize(message: types.Message, state: FSMContext) -> None:
    """Build CreateProductDto and call CreateProductUseCase."""
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

    use_case = CreateProductUseCase()
    try:
        product = use_case.execute(dto)
        await message.answer(
            f"✅ Продукт <b>{data.get('category_name', '')}</b> створено!\n"
            f"UUID: <code>{product.id}</code>\n"
            f"Статус: {product.status}"
        )
    except Exception as exc:
        logger.exception("Product creation failed")
        await message.answer(
            f"❌ Помилка при створенні: <code>{exc}</code>\n"
            "Спробуйте /start знову."
        )
    finally:
        await state.clear()
