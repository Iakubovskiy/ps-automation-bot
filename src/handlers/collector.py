"""Handlers for the item collection process."""
from datetime import datetime
from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from src.states import CollectorState
from src.enums import SheathColor, MountType, Status
from src.services.google_sheets import gs_service
from src.services.file_manager import generate_item_uuid, save_file_path
from src.keyboards.builders import (
    get_models_keyboard, get_enum_keyboard, get_yes_no_keyboard
)

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext) -> None:
    """Start the collection process and ask for model name."""
    await state.clear()
    models = await gs_service.get_models()
    
    if not models:
        await message.answer("Помилка: Список моделей в таблиці порожній.")
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

    # Клавіатура з кнопкою завершення
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Це всі фото ✅", callback_data="finish_photos")]
    ])
    await message.answer(f"Фото {photo_count} збережено. Бажаєте додати ще?", reply_markup=kb)

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
        await state.update_data(lanyard=choice)
        await callback.message.edit_text(
            "Оберіть тип кріплення:",
            reply_markup=get_enum_keyboard(MountType)
        )
        await state.set_state(CollectorState.mount_type)