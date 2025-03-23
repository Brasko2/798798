"""
Клавиатуры для работы с кластерами VPN
"""
from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_cluster_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для управления кластерами"""
    buttons = [
        [
            InlineKeyboardButton(text="➕ Добавить кластер", callback_data="cluster:add"),
            InlineKeyboardButton(text="📋 Список кластеров", callback_data="cluster:list")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin:menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_cluster_edit_keyboard(cluster_id: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру для редактирования кластера"""
    buttons = [
        [
            InlineKeyboardButton(
                text="✏️ Редактировать",
                callback_data=f"cluster:edit:{cluster_id}"
            ),
            InlineKeyboardButton(
                text="❌ Удалить",
                callback_data=f"cluster:delete:{cluster_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🖥️ Серверы",
                callback_data=f"cluster:servers:{cluster_id}"
            ),
            InlineKeyboardButton(
                text="📊 Статистика",
                callback_data=f"cluster:stats:{cluster_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="cluster:list"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons) 