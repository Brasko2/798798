"""
Клавиатуры для покупки VPN с улучшенным дизайном
"""

from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ..models.tariff import Tariff


def get_tariff_selection_kb(tariffs: List[Tariff]) -> InlineKeyboardMarkup:
    """
    Создает красивую клавиатуру для выбора тарифа
    
    Args:
        tariffs: Список доступных тарифов
        
    Returns:
        Инлайн-клавиатура с кнопками тарифов
    """
    builder = InlineKeyboardBuilder()
    
    # Добавляем emoji в зависимости от ценовой категории тарифа
    for tariff in tariffs:
        # Определяем эмодзи на основе типа тарифа
        if tariff.is_trial:
            emoji = "🎁"  # Пробный тариф
        elif tariff.price < 300:
            emoji = "🔹"  # Базовый тариф
        elif tariff.price < 700:
            emoji = "🔶"  # Стандартный тариф
        else:
            emoji = "💎"  # Премиум тариф
        
        # Форматируем информацию о тарифе
        price_text = f"{tariff.price:.0f}₽" if tariff.price == int(tariff.price) else f"{tariff.price:.2f}₽"
        duration_text = f"{tariff.duration_days} дн."
        devices_text = f"{tariff.max_devices} устр."
        
        # Создаем текст для кнопки
        button_text = f"{emoji} {tariff.name} • {price_text} • {duration_text} • {devices_text}"
        
        # Добавляем кнопку с колбэком, который содержит ID тарифа
        builder.button(
            text=button_text,
            callback_data=f"tariff:{tariff.id}"
        )
    
    # Кнопка для отмены
    builder.button(
        text="❌ Отмена",
        callback_data="back_to_main"
    )
    
    # Устанавливаем ширину строки в 1 кнопку
    builder.adjust(1)
    
    return builder.as_markup()


def get_payment_kb(payment_url: str) -> InlineKeyboardMarkup:
    """
    Создает красивую клавиатуру для оплаты
    
    Args:
        payment_url: URL для оплаты
        
    Returns:
        Инлайн-клавиатура с кнопками оплаты
    """
    builder = InlineKeyboardBuilder()
    
    # Кнопка для перехода к оплате
    builder.button(
        text="💳 Перейти к оплате",
        url=payment_url
    )
    
    # Кнопка для проверки оплаты
    builder.button(
        text="🔄 Проверить оплату",
        callback_data="check_payment"
    )
    
    # Кнопка для отмены платежа
    builder.button(
        text="❌ Отменить платеж",
        callback_data="cancel_payment"
    )
    
    # Устанавливаем ширину строки в 1 кнопку
    builder.adjust(1)
    
    return builder.as_markup()


def get_payment_success_kb() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для успешной оплаты
    
    Returns:
        Инлайн-клавиатура с кнопками после успешной оплаты
    """
    builder = InlineKeyboardBuilder()
    
    # Кнопка для просмотра подписок
    builder.button(
        text="🔑 Мои подписки",
        callback_data="my_subscriptions"
    )
    
    # Кнопка для просмотра инструкций
    builder.button(
        text="📲 Инструкции по настройке",
        callback_data="instructions"
    )
    
    # Кнопка для возврата в главное меню
    builder.button(
        text="🏠 Главное меню",
        callback_data="back_to_main"
    )
    
    # Устанавливаем ширину строки в 1 кнопку
    builder.adjust(1)
    
    return builder.as_markup() 