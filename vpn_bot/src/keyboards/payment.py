"""
Клавиатуры для работы с платежами
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_payment_keyboard(payment_id: str, is_recurring: bool = False) -> InlineKeyboardMarkup:
    """Создает клавиатуру для платежа"""
    buttons = [
        [
            InlineKeyboardButton(
                text="💳 Оплатить",
                callback_data=f"payment:pay:{payment_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔍 Проверить оплату",
                callback_data=f"payment:check:{payment_id}"
            )
        ]
    ]
    
    # Если это повторяющийся платеж (подписка), добавляем опцию рекуррентного платежа
    if is_recurring:
        buttons.insert(1, [
            InlineKeyboardButton(
                text="🔄 Подключить автоплатеж",
                callback_data=f"payment:recurring:{payment_id}"
            )
        ])
    
    # Добавляем кнопку отмены
    buttons.append([
        InlineKeyboardButton(
            text="❌ Отменить",
            callback_data="payment:cancel"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_check_payment_keyboard(payment_id: str) -> InlineKeyboardMarkup:
    """Создает клавиатуру для проверки платежа"""
    buttons = [
        [
            InlineKeyboardButton(
                text="🔍 Проверить ещё раз",
                callback_data=f"payment:check:{payment_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Отменить",
                callback_data="payment:cancel"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons) 