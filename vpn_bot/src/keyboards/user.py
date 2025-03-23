"""
Клавиатуры для работы с пользователями
"""
from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_user_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для пользователя"""
    buttons = [
        [
            InlineKeyboardButton(text="👤 Профиль", callback_data="user:profile"),
            InlineKeyboardButton(text="💰 Баланс", callback_data="user:balance")
        ],
        [
            InlineKeyboardButton(text="🔑 Подписки", callback_data="user:subscriptions"),
            InlineKeyboardButton(text="📋 История", callback_data="user:history")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="main:menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_subscription_keyboard(sub_id: int, has_active: bool = True) -> InlineKeyboardMarkup:
    """Создает клавиатуру для управления подпиской"""
    buttons = []
    
    # Если есть активная подписка, добавляем кнопки управления
    if has_active:
        buttons.extend([
            [
                InlineKeyboardButton(
                    text="📊 Информация",
                    callback_data=f"sub:info:{sub_id}"
                ),
                InlineKeyboardButton(
                    text="📱 Устройства",
                    callback_data=f"sub:devices:{sub_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📝 Инструкция",
                    callback_data=f"sub:instructions:{sub_id}"
                ),
                InlineKeyboardButton(
                    text="🔄 Продлить",
                    callback_data=f"sub:renew:{sub_id}"
                )
            ]
        ])
    else:
        # Если нет активной подписки, предлагаем купить
        buttons.append([
            InlineKeyboardButton(
                text="💰 Купить подписку",
                callback_data="tariff:list"
            )
        ])
    
    # Кнопка возврата
    buttons.append([
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="user:subscriptions"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons) 