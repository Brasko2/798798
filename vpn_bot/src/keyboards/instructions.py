"""
Клавиатуры для работы с инструкциями
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_instructions_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для выбора платформы"""
    buttons = [
        [
            InlineKeyboardButton(text="📱 Android", callback_data="instruction:android"),
            InlineKeyboardButton(text="📱 iOS", callback_data="instruction:ios")
        ],
        [
            InlineKeyboardButton(text="💻 Windows", callback_data="instruction:windows"),
            InlineKeyboardButton(text="💻 macOS", callback_data="instruction:macos")
        ],
        [
            InlineKeyboardButton(text="💻 Linux", callback_data="instruction:linux"),
            InlineKeyboardButton(text="🖥️ Роутер", callback_data="instruction:router")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="main:menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_instructions_back_keyboard(platform: str) -> InlineKeyboardMarkup:
    """Создает клавиатуру с кнопкой назад к списку инструкций"""
    buttons = [
        [
            InlineKeyboardButton(text="📥 Скачать", callback_data=f"instruction:download:{platform}")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад к инструкциям", callback_data="instruction:list")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons) 