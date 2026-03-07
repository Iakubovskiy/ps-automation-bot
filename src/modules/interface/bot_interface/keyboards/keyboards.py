"""Keyboard builders for the dynamic bot interface.

Extends the original keyboard patterns to work with database-driven options
(StaticReference labels) instead of hardcoded enums.
"""
from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def get_category_keyboard(categories: list[dict]) -> InlineKeyboardMarkup:
    """Build a keyboard for category selection.

    Args:
        categories: List of dicts with 'id' and 'name' keys.
    """
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(
            text=cat["name"],
            callback_data=f"cat_{cat['id']}",
        )
    builder.adjust(1)
    return builder.as_markup()


def get_static_ref_keyboard(
    references: list[dict],
    prefix: str = "ref_",
) -> InlineKeyboardMarkup:
    """Build a keyboard from StaticReference options.

    Args:
        references: List of dicts with 'key' and 'label' keys.
        prefix: Callback data prefix.
    """
    builder = InlineKeyboardBuilder()
    for ref in references:
        builder.button(
            text=ref["label"],
            callback_data=f"{prefix}{ref['key']}",
        )
    builder.adjust(2)
    return builder.as_markup()


def get_multi_select_ref_keyboard(
    references: list[dict],
    selected: set[str] | None = None,
    prefix: str = "mref_",
    done_callback: str = "mref_done",
) -> InlineKeyboardMarkup:
    """Multi-select keyboard from StaticReference options.

    Args:
        references: List of dicts with 'key' and 'label' keys.
        selected: Set of currently selected keys.
        prefix: Callback data prefix for toggle.
        done_callback: Callback for the confirmation button.
    """
    if selected is None:
        selected = set()
    builder = InlineKeyboardBuilder()
    for ref in references:
        icon = "✅" if ref["key"] in selected else "⬜"
        builder.button(
            text=f"{icon} {ref['label']}",
            callback_data=f"{prefix}{ref['key']}",
        )
    builder.adjust(2)
    builder.row(
        types.InlineKeyboardButton(text="Готово ➡️", callback_data=done_callback)
    )
    return builder.as_markup()


def get_boolean_keyboard() -> InlineKeyboardMarkup:
    """Boolean field keyboard (Так/Ні)."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Так", callback_data="bool_yes")
    builder.button(text="❌ Ні", callback_data="bool_no")
    builder.adjust(2)
    return builder.as_markup()


def get_boolean_keyboard_with_skip() -> InlineKeyboardMarkup:
    """Boolean field keyboard with skip option."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Так", callback_data="bool_yes")
    builder.button(text="❌ Ні", callback_data="bool_no")
    builder.adjust(2)
    builder.row(types.InlineKeyboardButton(text="⏩ Пропустити", callback_data="skip_attr"))
    return builder.as_markup()


def get_finish_files_keyboard() -> InlineKeyboardMarkup:
    """Button to finish file_array upload."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="Це всі файли ✅", callback_data="finish_files")]
        ]
    )


def get_yes_no_keyboard() -> InlineKeyboardMarkup:
    """Simple Yes/No keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Так", callback_data="yes")
    builder.button(text="❌ Ні", callback_data="no")
    return builder.as_markup()


def get_finish_photos_keyboard() -> InlineKeyboardMarkup:
    """Button to finish photo upload."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="Це всі фото ✅", callback_data="finish_photos")]
        ]
    )


def get_video_choice_keyboard() -> InlineKeyboardMarkup:
    """Upload video or skip."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="🎬 Завантажити відео", callback_data="upload_video")],
            [types.InlineKeyboardButton(text="⏩ Пропустити", callback_data="skip_video")],
        ]
    )


def get_skip_keyboard(callback: str = "skip") -> InlineKeyboardMarkup:
    """A single 'Skip' button."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="⏩ Пропустити", callback_data=callback)]
        ]
    )

