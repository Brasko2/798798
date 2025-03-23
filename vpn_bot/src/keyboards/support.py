"""
Клавиатуры для раздела поддержки
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Dict


def get_support_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для раздела поддержки
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками поддержки
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="❓ Часто задаваемые вопросы",
            callback_data="support:faq"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="📝 Новое обращение",
            callback_data="support:new_ticket"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="📋 Мои обращения",
            callback_data="support:my_tickets"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="📲 Инструкции по настройке",
            callback_data="instructions"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="main_menu"
        )
    )
    
    return builder.as_markup()


def get_support_ticket_keyboard(ticket_buttons: List[Dict[str, str]]) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру со списком обращений пользователя
    
    Args:
        ticket_buttons: Список словарей с параметрами кнопок обращений
        
    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками обращений
    """
    builder = InlineKeyboardBuilder()
    
    # Добавляем кнопки обращений
    for button in ticket_buttons:
        builder.row(
            InlineKeyboardButton(
                text=button["text"],
                callback_data=button["callback_data"]
            )
        )
    
    # Добавляем кнопку создания нового обращения
    builder.row(
        InlineKeyboardButton(
            text="📝 Новое обращение",
            callback_data="support:new_ticket"
        )
    )
    
    # Добавляем кнопку возврата
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="support"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="main_menu"
        )
    )
    
    return builder.as_markup()


def get_callback_keyboard(callback_data: str) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с одной кнопкой отмены
    
    Args:
        callback_data: Данные для обратного вызова
        
    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопкой отмены
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="❌ Отменить",
            callback_data=callback_data
        )
    )
    
    return builder.as_markup() 