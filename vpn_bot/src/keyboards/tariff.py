"""
Клавиатуры для работы с тарифами
"""
from typing import List, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_tariff_keyboard(tariff_id: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру для работы с тарифом"""
    buttons = [
        [
            InlineKeyboardButton(text="📝 Купить", callback_data=f"tariff:buy:{tariff_id}"),
            InlineKeyboardButton(text="ℹ️ Подробнее", callback_data=f"tariff:info:{tariff_id}")
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="tariff:list")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_pagination_keyboard(
    current_page: int,
    total_pages: int,
    prefix: str = "page",
    additional_buttons: Optional[List[List[InlineKeyboardButton]]] = None
) -> InlineKeyboardMarkup:
    """Создает клавиатуру с пагинацией"""
    nav_buttons = []
    
    # Кнопка "Назад", если не на первой странице
    if current_page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"{prefix}:{current_page - 1}"
            )
        )
    
    # Текущая страница и общее количество
    nav_buttons.append(
        InlineKeyboardButton(
            text=f"{current_page}/{total_pages}",
            callback_data="noop"
        )
    )
    
    # Кнопка "Вперед", если не на последней странице
    if current_page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                text="➡️ Вперед",
                callback_data=f"{prefix}:{current_page + 1}"
            )
        )
    
    buttons = []
    if additional_buttons:
        buttons.extend(additional_buttons)
    
    buttons.append(nav_buttons)
    
    return InlineKeyboardMarkup(inline_keyboard=buttons) 