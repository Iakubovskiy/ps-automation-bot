"""Handlers for the item collection process."""
import asyncio
import logging
from collections import defaultdict
from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from src.states import CollectorState
from src.enums import SheathColor, MountType
from src.repositories.google_sheets import gs_service
from src.services.file_manager import generate_item_uuid, save_file_path
from src.dto.input_product_data import InputProductData
from src.services.gemini_service import GeminiService
from src.services.product_manager import ProductManager
from src.keyboards.builders import (
    get_models_keyboard, get_enum_keyboard, get_yes_no_keyboard,
    get_multi_select_keyboard,
)

logger = logging.getLogger(__name__)
router = Router()

_photo_locks: dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)
_photo_debounce_tasks: dict[int, asyncio.Task] = {}


# ── /start ───────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext) -> None:
    """Start the collection process and ask for model name."""
    await state.clear()
    models = await gs_service.get_models()

    if not gs_service.available:
        await message.answer(
            "⚠️ Google Sheets не підключено — бот працює з тестовими даними."
        )

    if not models:
        await message.answer("Помилка: Список моделей порожній.")
        return

    item_uuid = generate_item_uuid()
    await state.update_data(item_uuid=item_uuid, photos=[])

    await message.answer(
        "Привіт! Починаємо збір даних. Оберіть назву виробу:",
        reply_markup=get_models_keyboard(models)
    )
    await state.set_state(CollectorState.name)


# ── Name ─────────────────────────────────────────────────────────────

@router.callback_query(CollectorState.name, F.data.startswith("model_"))
async def process_name(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Save model name and ask for price."""
    model_name = callback.data.replace("model_", "")
    await state.update_data(model_name=model_name)

    await callback.answer()
    await callback.message.answer(f"Ви обрали: {model_name}. Тепер введіть ціну (цифрами):")
    await state.set_state(CollectorState.price)


# ── Price ────────────────────────────────────────────────────────────

@router.message(CollectorState.price)
async def process_price(message: types.Message, state: FSMContext) -> None:
    """Validate price and ask for sheath color."""
    if not message.text.isdigit():
        await message.answer("Будь ласка, введіть числове значення для ціни.")
        return

    await state.update_data(price=int(message.text))
    await message.answer(
        "Оберіть колір чохла:",
        reply_markup=get_enum_keyboard(SheathColor)
    )
    await state.set_state(CollectorState.sheath_color)


# ── Sheath color ─────────────────────────────────────────────────────

@router.callback_query(CollectorState.sheath_color)
async def process_color(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Save color and ask for blade engraving count."""
    await state.update_data(sheath_color=callback.data)
    await callback.answer()
    await callback.message.answer(
        "Скільки гравіювань на клинку? (введіть число, 0 — якщо немає):"
    )
    await state.set_state(CollectorState.blade_engravings)


# ── Engravings ───────────────────────────────────────────────────────

@router.message(CollectorState.blade_engravings)
async def process_blade_engravings(message: types.Message, state: FSMContext) -> None:
    """Save blade engraving count and ask for sheath engravings."""
    if not message.text.isdigit():
        await message.answer("Будь ласка, введіть числове значення.")
        return

    await state.update_data(blade_engravings=int(message.text))
    await message.answer(
        "Скільки гравіювань на піхвах? (введіть число, 0 — якщо немає):"
    )
    await state.set_state(CollectorState.sheath_engravings)


@router.message(CollectorState.sheath_engravings)
async def process_sheath_engravings(message: types.Message, state: FSMContext) -> None:
    """Save sheath engraving count and ask about Musat."""
    if not message.text.isdigit():
        await message.answer("Будь ласка, введіть числове значення.")
        return

    await state.update_data(sheath_engravings=int(message.text))
    await message.answer(
        "Чи є в комплекті мусат?",
        reply_markup=get_yes_no_keyboard()
    )
    await state.set_state(CollectorState.accessories)


# ── Accessories (musat → firesteel → lanyard) ────────────────────────

@router.callback_query(CollectorState.accessories)
async def process_accessories(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Step-by-step collection of boolean flags."""
    data = await state.get_data()
    choice = callback.data == "yes"

    if "musat" not in data:
        await state.update_data(musat=choice)
        await callback.answer()
        await callback.message.answer(
            "Чи є в комплекті кресало?", reply_markup=get_yes_no_keyboard()
        )
    elif "firesteel" not in data:
        await state.update_data(firesteel=choice)
        await callback.answer()
        await callback.message.answer(
            "Чи є в комплекті темляк?", reply_markup=get_yes_no_keyboard()
        )
    else:
        await state.update_data(lanyard=choice, selected_mounts=[])
        await callback.answer()
        await callback.message.answer(
            "Оберіть тип(и) кріплення (можна декілька), потім натисніть 'Готово':",
            reply_markup=get_multi_select_keyboard(MountType)
        )
        await state.set_state(CollectorState.mount_type)


# ── Mount type (multi-select) ────────────────────────────────────────

@router.callback_query(CollectorState.mount_type, F.data.startswith("mtoggle_"))
async def toggle_mount(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Toggle a mount type on/off in the multi-select list."""
    value = callback.data.replace("mtoggle_", "")
    data = await state.get_data()
    selected: list[str] = data.get("selected_mounts", [])

    if value in selected:
        selected.remove(value)
    else:
        selected.append(value)

    await state.update_data(selected_mounts=selected)
    await callback.message.edit_reply_markup(
        reply_markup=get_multi_select_keyboard(MountType, set(selected))
    )
    await callback.answer()


@router.callback_query(CollectorState.mount_type, F.data == "mount_done")
async def confirm_mount(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Confirm selected mount types and proceed to steel selection."""
    data = await state.get_data()
    selected: list[str] = data.get("selected_mounts", [])

    if not selected:
        await callback.answer("Оберіть хоча б один тип кріплення!", show_alert=True)
        return

    mount_str = ", ".join(selected)
    await state.update_data(mount_type=mount_str)
    await callback.answer()
    await callback.message.answer(f"Обрано кріплення: {mount_str}")

    # → Next step: steel selection
    steels = await gs_service.get_steel_options()
    if not steels:
        await callback.message.answer("Помилка: Список сталей порожній.")
        return

    await callback.message.answer(
        "Оберіть тип сталі:",
        reply_markup=get_models_keyboard(steels, prefix="steel_")
    )
    await state.set_state(CollectorState.steel)


# ── Steel selection ──────────────────────────────────────────────────

@router.callback_query(CollectorState.steel, F.data.startswith("steel_"))
async def process_steel(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Save steel choice and proceed to handle material."""
    steel = callback.data.replace("steel_", "")
    await state.update_data(steel=steel)
    await callback.answer()
    await callback.message.answer(f"Обрано сталь: {steel}")

    handles = await gs_service.get_handle_options()
    if not handles:
        await callback.message.answer("Помилка: Список матеріалів руків'я порожній.")
        return

    await callback.message.answer(
        "Оберіть матеріал руків'я:",
        reply_markup=get_models_keyboard(handles, prefix="handle_")
    )
    await state.set_state(CollectorState.handle_material)


# ── Handle material selection ────────────────────────────────────────

@router.callback_query(CollectorState.handle_material, F.data.startswith("handle_"))
async def process_handle(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Save handle material and proceed to photos."""
    handle = callback.data.replace("handle_", "")
    await state.update_data(handle_material=handle)
    await callback.answer()
    await callback.message.answer(f"Обрано матеріал: {handle}")

    await state.set_state(CollectorState.media_photos)
    await callback.message.answer(
        "Тепер надішліть фото виробу (можна декілька). "
        "Коли закінчите — натисніть кнопку нижче."
    )


# ── Photos ───────────────────────────────────────────────────────────

@router.message(CollectorState.media_photos, F.photo)
async def process_photos(message: types.Message, state: FSMContext, bot) -> None:
    """Save photos to local storage."""
    user_id = message.from_user.id
    async with _photo_locks[user_id]:
        data = await state.get_data()
        item_uuid = data['item_uuid']
        photo_count = len(data.get('photos', [])) + 1

        file_id = message.photo[-1].file_id
        file = await bot.get_file(file_id)

        file_name = f"photo_{photo_count}.jpg"
        dest = save_file_path(item_uuid, file_name)

        await bot.download_file(file.file_path, dest)

        photos = data.get('photos', [])
        photos.append(dest)
        await state.update_data(photos=photos)

        # --- Debounce: wait for user to finish sending photos ---
        prev_task = _photo_debounce_tasks.get(user_id)
        if prev_task and not prev_task.done():
            prev_task.cancel()

        _photo_debounce_tasks[user_id] = asyncio.create_task(
            _send_photo_summary(message, state, user_id)
        )


async def _send_photo_summary(
    message: types.Message, state: FSMContext, user_id: int
) -> None:
    """Wait for a short pause, then send a single summary with the finish button."""
    await asyncio.sleep(1.5)

    async with _photo_locks[user_id]:
        data = await state.get_data()
        total = len(data.get('photos', []))

    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Це всі фото ✅", callback_data="finish_photos")]
    ])
    await message.answer(
        f"📸 Збережено фото: {total} шт. Бажаєте додати ще?",
        reply_markup=kb,
    )


@router.callback_query(CollectorState.media_photos, F.data == "finish_photos")
async def finish_photos(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Photos collected — ask about video."""
    data = await state.get_data()
    count = len(data.get("photos", []))
    await callback.answer()
    await callback.message.answer(f"\u2705 Збережено фото: {count} шт.")

    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="\U0001f3ac Завантажити відео", callback_data="upload_video")],
        [types.InlineKeyboardButton(text="\u23e9 Пропустити", callback_data="skip_video")],
    ])
    await callback.message.answer("Бажаєте завантажити відео?", reply_markup=kb)
    await state.set_state(CollectorState.media_video)


# ── Video ────────────────────────────────────────────────────────────

@router.callback_query(CollectorState.media_video, F.data == "upload_video")
async def ask_for_video(callback: types.CallbackQuery, state: FSMContext) -> None:
    """User chose to upload a video."""
    await callback.answer()
    await callback.message.answer("Надішліть відео:")


@router.message(CollectorState.media_video, F.video)
async def process_video(message: types.Message, state: FSMContext, bot) -> None:
    """Save the uploaded video."""
    data = await state.get_data()
    item_uuid = data["item_uuid"]

    file = await bot.get_file(message.video.file_id)
    ext = file.file_path.rsplit(".", 1)[-1] if "." in file.file_path else "mp4"
    dest = save_file_path(item_uuid, f"video.{ext}")
    await bot.download_file(file.file_path, dest)
    await state.update_data(video_path=dest)

    await message.answer("\u2705 Відео збережено.")
    await _ask_youtube(message, state)


@router.callback_query(CollectorState.media_video, F.data == "skip_video")
async def skip_video(callback: types.CallbackQuery, state: FSMContext) -> None:
    """User skipped video upload."""
    await callback.answer()
    await callback.message.answer("Відео пропущено.")
    await _ask_youtube(callback.message, state)


# ── YouTube link ─────────────────────────────────────────────────────

async def _ask_youtube(message: types.Message, state: FSMContext) -> None:
    """Ask for a YouTube link or skip."""
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="\u23e9 Пропустити", callback_data="skip_youtube")],
    ])
    await message.answer(
        "Введіть посилання на YouTube-відео або натисніть 'Пропустити':",
        reply_markup=kb,
    )
    await state.set_state(CollectorState.youtube_link)


@router.message(CollectorState.youtube_link, F.text)
async def process_youtube(message: types.Message, state: FSMContext) -> None:
    """Save YouTube link and finalize."""
    link = message.text.strip()
    if "youtu" not in link:
        await message.answer("Це не схоже на YouTube-посилання. Спробуйте ще раз або натисніть 'Пропустити'.")
        return
    await state.update_data(youtube_link=link)
    await message.answer(f"\u2705 Посилання збережено: {link}")
    await _finalize(message, state)


@router.callback_query(CollectorState.youtube_link, F.data == "skip_youtube")
async def skip_youtube(callback: types.CallbackQuery, state: FSMContext) -> None:
    """User skipped YouTube link."""
    await callback.answer()
    await callback.message.answer("YouTube пропущено.")
    await _finalize(callback.message, state)


# ── Build InputProductData ───────────────────────────────────────────

def _build_input_data(data: dict, blade_specs: dict) -> InputProductData:
    """Map bot-collected state + Sheets specs → InputProductData DTO."""
    mount_str = data.get("mount_type", "")
    attachments = [m.strip() for m in mount_str.split(",") if m.strip()]

    engraving_count = (
        data.get("blade_engravings", 0) + data.get("sheath_engravings", 0)
    )

    return InputProductData(
        product_code=data["item_uuid"],
        blade_name=data["model_name"],
        price=float(data.get("price", 0)),
        sheath_type=data.get("sheath_color", ""),
        attachments=attachments,
        has_honing_rod=data.get("musat", False),
        has_lanyard=data.get("lanyard", False),
        has_flint=data.get("firesteel", False),
        engraving_count=engraving_count,
        steel=data.get("steel", ""),
        handle_material=data.get("handle_material"),
        photos=data.get("photos", []),
        video_path=data.get("video_path", ""),
        video_url=data.get("youtube_link", ""),
        # Sheets-sourced fields
        total_length=blade_specs.get("total_length", 0),
        blade_length=blade_specs.get("blade_length", 0),
        blade_width=blade_specs.get("blade_width", 0),
        blade_weight=blade_specs.get("blade_weight", 0),
        blade_thickness=blade_specs.get("blade_thickness", 0.0),
        hardness=blade_specs.get("hardness", 0),
        sharpening_angle=blade_specs.get("sharpening_angle", 0),
        configuration_type=blade_specs.get("configuration_type"),
        blade_type=blade_specs.get("blade_type", ""),
    )


# ── Finalize ─────────────────────────────────────────────────────────

async def _finalize(message: types.Message, state: FSMContext) -> None:
    """Build InputProductData, send to ProductManager, and notify user."""
    data = await state.get_data()
    model_name = data["model_name"]

    await message.answer("⏳ Отримую характеристики клинка…")
    blade_specs = await gs_service.get_blade_specs(model_name)

    input_data = _build_input_data(data, blade_specs)

    await message.answer(
        f"🚀 Запускаю обробку виробу <b>{model_name}</b>…\n"
        f"UUID: <code>{data['item_uuid']}</code>"
    )

    manager = ProductManager(ai_service=GeminiService())
    try:
        await manager.process(input_data)
        await message.answer(f"\u2705 Виріб <b>{model_name}</b> успішно оброблено!")
    except Exception as exc:
        logger.exception("Pipeline error for %s", model_name)
        await message.answer(
            f"❌ Помилка при обробці: <code>{exc}</code>\n"
            "Спробуйте /start знову."
        )
    finally:
        await state.clear()
