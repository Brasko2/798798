"""
Клавиатуры для раздела бонусов и акций
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_bonus_keyboard(has_bonus_days: bool = False) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для раздела бонусов и акций
    
    Args:
        has_bonus_days: Флаг наличия бонусных дней у пользователя
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками бонусов
    """
    builder = InlineKeyboardBuilder()
    
    # Кнопки информации о бонусах
    builder.row(
        InlineKeyboardButton(
            text="👥 Реферальная программа",
            callback_data="bonus:referral"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="⭐ Бонус за отзыв",
            callback_data="bonus:review"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🔄 Программа лояльности",
            callback_data="bonus:loyalty"
        )
    )
    
    # Кнопка применения бонуса (только если есть бонусные дни)
    if has_bonus_days:
        builder.row(
            InlineKeyboardButton(
                text="🎁 Применить бонусные дни",
                callback_data="bonus:apply"
            )
        )
    
    # Кнопка возврата в главное меню
    builder.row(
        InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="main_menu"
        )
    )
    
    return builder.as_markup()


def get_back_to_bonus_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с кнопкой возврата к списку бонусов
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопкой возврата
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад к бонусам",
            callback_data="bonus"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="main_menu"
        )
    )
    
    return builder.as_markup() 