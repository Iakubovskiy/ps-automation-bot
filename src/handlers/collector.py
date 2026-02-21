"""Handlers for the item collection process."""
import asyncio
from collections import defaultdict
from datetime import datetime
from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from src.states import CollectorState
from src.enums import SheathColor, MountType, Status
from src.services.google_sheets import gs_service
from src.services.file_manager import generate_item_uuid, save_file_path
from src.keyboards.builders import (
    get_models_keyboard, get_enum_keyboard, get_yes_no_keyboard,
    get_multi_select_keyboard,
)

router = Router()

# Lock per user to prevent race conditions when multiple photos arrive simultaneously
_photo_locks: dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)
# Debounce tasks — wait for all photos in a batch before showing the confirmation
_photo_debounce_tasks: dict[int, asyncio.Task] = {}

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

@router.callback_query(CollectorState.name, F.data.startswith("model_"))
async def process_name(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Save model name and ask for price."""
    model_name = callback.data.replace("model_", "")
    await state.update_data(model_name=model_name)
    
    await callback.message.edit_text(f"Ви обрали: {model_name}. Тепер введіть ціну (цифрами):")
    await state.set_state(CollectorState.price)

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

@router.message(CollectorState.media_photos, F.photo)
async def process_photos(message: types.Message, state: FSMContext, bot) -> None:
    """Save photos to local storage."""
    user_id = message.from_user.id
    async with _photo_locks[user_id]:
        data = await state.get_data()
        item_uuid = data['item_uuid']
        photo_count = len(data.get('photos', [])) + 1

        # Отримуємо файл з серверів Telegram
        file_id = message.photo[-1].file_id
        file = await bot.get_file(file_id)

        # Формуємо шлях: media/{uuid}/photo_1.jpg
        file_name = f"photo_{photo_count}.jpg"
        dest = save_file_path(item_uuid, file_name)

        await bot.download_file(file.file_path, dest)

        # Оновлюємо список фото в пам'яті
        photos = data.get('photos', [])
        photos.append(dest)
        await state.update_data(photos=photos)

        # --- Debounce: все під локом, щоб не було дублів ---

        # Скасовуємо попередній таймер
        prev_task = _photo_debounce_tasks.get(user_id)
        if prev_task and not prev_task.done():
            prev_task.cancel()

        # Видаляємо попереднє повідомлення-підсумок
        prev_summary_id = (await state.get_data()).get('_photo_summary_msg_id')
        if prev_summary_id:
            try:
                await message.bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=prev_summary_id,
                )
            except Exception:
                pass
            await state.update_data(_photo_summary_msg_id=None)

        # Запускаємо новий таймер
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
    sent = await message.answer(
        f"📸 Збережено фото: {total} шт. Бажаєте додати ще?",
        reply_markup=kb,
    )
    # Зберігаємо id повідомлення, щоб прибрати кнопку при новій фотці
    async with _photo_locks[user_id]:
        await state.update_data(_photo_summary_msg_id=sent.message_id)


@router.callback_query(CollectorState.media_photos, F.data == "finish_photos")
async def finish_photos(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Photos collected — ask about video."""
    data = await state.get_data()
    count = len(data.get("photos", []))
    await callback.message.edit_text(f"\u2705 Збережено фото: {count} шт.")
    await callback.answer()

    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="\U0001f3ac Завантажити відео", callback_data="upload_video")],
        [types.InlineKeyboardButton(text="\u23e9 Пропустити", callback_data="skip_video")],
    ])
    await callback.message.answer("Бажаєте завантажити відео?", reply_markup=kb)
    await state.set_state(CollectorState.media_video)


@router.callback_query(CollectorState.media_video, F.data == "upload_video")
async def ask_for_video(callback: types.CallbackQuery, state: FSMContext) -> None:
    """User chose to upload a video."""
    await callback.message.edit_text("Надішліть відео:")
    await callback.answer()


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
    await callback.message.edit_text("Відео пропущено.")
    await callback.answer()
    await _ask_youtube(callback.message, state)


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
    await callback.message.edit_text("YouTube пропущено.")
    await callback.answer()
    await _finalize(callback.message, state)


async def finalize_to_sheets(state: FSMContext) -> None:
    """Collect all data and write to Google Sheets."""
    data = await state.get_data()
    
    # Підготовка рядка згідно з порядком колонок у ТЗ
    row = [
        data['item_uuid'],
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data['model_name'],
        data['price'],
        data.get('sheath_color'),
        data.get('blade_engravings', 0),
        data.get('sheath_engravings', 0),
        data.get('musat', False),
        data.get('firesteel', False),
        data.get('lanyard', False),
        data.get('mount_type'),
        data.get('youtube_link', ""),
        Status.PENDING.value
    ]
    
    await gs_service.append_item(row)
    
    # Заглушка для подальшої обробки ШІ
    print(f"DEBUG: Starting process_item for UUID: {data['item_uuid']}")


async def _finalize(message: types.Message, state: FSMContext) -> None:
    """Final step — save to sheets and notify user."""
    await finalize_to_sheets(state)
    data = await state.get_data()
    await message.answer(
        f"\u2705 Готово! Виріб <b>{data['model_name']}</b> збережено.\n"
        f"UUID: <code>{data['item_uuid']}</code>"
    )
    await state.clear()

@router.callback_query(CollectorState.sheath_color)
async def process_color(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Save color and ask about Musat."""
    await state.update_data(sheath_color=callback.data)
    await callback.message.edit_text(
        "Чи є в комплекті мусат?",
        reply_markup=get_yes_no_keyboard()
    )
    await state.set_state(CollectorState.accessories)

@router.callback_query(CollectorState.accessories)
async def process_accessories(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Step-by-step collection of boolean flags."""
    data = await state.get_data()
    choice = callback.data == "yes"
    
    if "musat" not in data:
        await state.update_data(musat=choice)
        await callback.message.edit_text("Чи є в комплекті кресало?", reply_markup=get_yes_no_keyboard())
    elif "firesteel" not in data:
        await state.update_data(firesteel=choice)
        await callback.message.edit_text("Чи є в комплекті темляк?", reply_markup=get_yes_no_keyboard())
    else:
        await state.update_data(lanyard=choice, selected_mounts=[])
        await callback.message.edit_text(
            "Оберіть тип(и) кріплення (можна декілька), потім натисніть 'Готово':",
            reply_markup=get_multi_select_keyboard(MountType)
        )
        await state.set_state(CollectorState.mount_type)


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
    """Confirm selected mount types and proceed."""
    data = await state.get_data()
    selected: list[str] = data.get("selected_mounts", [])

    if not selected:
        await callback.answer("Оберіть хоча б один тип кріплення!", show_alert=True)
        return

    mount_str = ", ".join(selected)
    await state.update_data(mount_type=mount_str)
    await callback.message.edit_text(f"Обрано кріплення: {mount_str}")
    await callback.answer()
    # TODO: перехід до наступного кроку (media_photos / youtube_link)
    await state.set_state(CollectorState.media_photos)
    await callback.message.answer(
        "Тепер надішліть фото виробу (можна декілька). "
        "Коли закінчите — натисніть кнопку нижче."
    )
