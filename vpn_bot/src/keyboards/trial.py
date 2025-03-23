"""
Клавиатуры для работы с пробным периодом
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_trial_kb(tariff_id: int) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для активации пробного периода
    
    Args:
        tariff_id: ID пробного тарифа
        
    Returns:
        Инлайн-клавиатура с кнопкой активации
    """
    builder = InlineKeyboardBuilder()
    
    # Кнопка активации пробного периода
    builder.button(
        text="🎁 Активировать пробный период",
        callback_data=f"activate_trial:{tariff_id}"
    )
    
    # Кнопка для перехода к обычным тарифам
    builder.button(
        text="🛒 Посмотреть платные тарифы",
        callback_data="show_plans"
    )
    
    # Кнопка отмены
    builder.button(
        text="❌ Отмена",
        callback_data="back_to_main"
    )
    
    # Устанавливаем ширину строки в 1 кнопку
    builder.adjust(1)
    
    return builder.as_markup()


def get_trial_success_kb() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру после успешной активации пробного периода
    
    Returns:
        Инлайн-клавиатура с кнопками
    """
    builder = InlineKeyboardBuilder()
    
    # Кнопка для просмотра инструкции
    builder.button(
        text="📚 Инструкция по настройке",
        callback_data="instructions"
    )
    
    # Кнопка для просмотра подписок
    builder.button(
        text="📋 Мои подписки",
        callback_data="subscriptions"
    )
    
    # Кнопка для перехода в главное меню
    builder.button(
        text="🏠 Главное меню",
        callback_data="back_to_main"
    )
    
    # Устанавливаем ширину строки в 1 кнопку
    builder.adjust(1)
    
    return builder.as_markup() 