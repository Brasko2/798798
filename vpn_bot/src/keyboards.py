from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    KeyboardButton,
    ReplyKeyboardMarkup
)

def main_keyboard(is_admin=False):
    """Основная клавиатура бота"""
    buttons = [
        [KeyboardButton(text="🛒 Купить подписку"), KeyboardButton(text="💻 Инструкция")],
        [KeyboardButton(text="💰 Мой баланс"), KeyboardButton(text="🔑 Мои подписки")],
        [KeyboardButton(text="📞 Поддержка"), KeyboardButton(text="ℹ️ О сервисе")]
    ]
    
    if is_admin:
        buttons.append([KeyboardButton(text="👑 Админ панель")])
    
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def admin_keyboard():
    """Клавиатура для админ-панели"""
    buttons = [
        [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="👥 Пользователи")],
        [KeyboardButton(text="💵 Финансы"), KeyboardButton(text="🔧 Настройки")],
        [KeyboardButton(text="🏠 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def tariff_selection_keyboard(tariffs):
    """Клавиатура для выбора тарифа"""
    buttons = []
    for tariff in tariffs:
        buttons.append([
            InlineKeyboardButton(
                text=f"{tariff['name']} - {tariff['price']} руб. ({tariff['duration']} дней)",
                callback_data=f"tariff:{tariff['id']}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def payment_keyboard(payment_url, payment_id):
    """Клавиатура для оплаты"""
    buttons = [
        [InlineKeyboardButton(text="💳 Оплатить", url=payment_url)],
        [InlineKeyboardButton(text="🔄 Проверить оплату", callback_data=f"check_payment:{payment_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def support_keyboard():
    """Клавиатура для раздела поддержки"""
    buttons = [
        [KeyboardButton(text="📝 Создать тикет")],
        [KeyboardButton(text="📋 Мои тикеты")],
        [KeyboardButton(text="🏠 Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def ticket_keyboard(ticket_id):
    """Клавиатура для управления тикетом"""
    buttons = [
        [InlineKeyboardButton(text="✏️ Ответить", callback_data=f"reply_ticket:{ticket_id}")],
        [InlineKeyboardButton(text="✅ Закрыть тикет", callback_data=f"close_ticket:{ticket_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def instruction_keyboard():
    """Клавиатура для выбора операционной системы при запросе инструкций"""
    buttons = [
        [
            InlineKeyboardButton(text="📱 Android", callback_data="instruction:android"),
            InlineKeyboardButton(text="🍎 iOS", callback_data="instruction:ios")
        ],
        [
            InlineKeyboardButton(text="🪟 Windows", callback_data="instruction:windows"),
            InlineKeyboardButton(text="🍏 macOS", callback_data="instruction:macos")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons) 