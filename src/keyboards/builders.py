"""Module for building telegram keyboards."""
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from src.enums import SheathColor, MountType

def get_enum_keyboard(enum_class) -> InlineKeyboardMarkup:
    """Generic function to create a keyboard from an Enum."""
    builder = InlineKeyboardBuilder()
    for item in enum_class:
        # callback_data буде значенням з Enum (напр. "Чорний")
        builder.button(text=item.value, callback_data=item.value)
    builder.adjust(2)  # Кнопки у два стовпчики
    return builder.as_markup()

def get_models_keyboard(models: list[str]) -> InlineKeyboardMarkup:
    """Create a keyboard with knife model names."""
    builder = InlineKeyboardBuilder()
    for model in models:
        builder.button(text=model, callback_data=f"model_{model}")
    builder.adjust(1)
    return builder.as_markup()

def get_yes_no_keyboard() -> InlineKeyboardMarkup:
    """Simple Yes/No keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Так", callback_data="yes")
    builder.button(text="❌ Ні", callback_data="no")
    return builder.as_markup()