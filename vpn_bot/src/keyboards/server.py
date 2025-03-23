"""
Клавиатуры для работы с серверами и кластерами
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List

from ..models.cluster import VPNCluster, VPNServer


def get_cluster_selection_kb(clusters: List[VPNCluster]) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для выбора кластера
    
    Args:
        clusters: Список объектов кластеров
        
    Returns:
        Инлайн-клавиатура с кнопками выбора кластера
    """
    builder = InlineKeyboardBuilder()
    
    # Добавляем кнопки для каждого кластера
    for cluster in clusters:
        builder.button(
            text=f"{cluster.name}",
            callback_data=f"cluster:{cluster.id}"
        )
    
    # Добавляем кнопку возврата
    builder.button(
        text="◀️ Назад",
        callback_data="back_to_main"
    )
    
    # Устанавливаем ширину строки в 1 кнопку
    builder.adjust(1)
    
    return builder.as_markup()


def get_server_selection_kb(servers: List[VPNServer]) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для выбора сервера
    
    Args:
        servers: Список объектов серверов
        
    Returns:
        Инлайн-клавиатура с кнопками выбора сервера
    """
    builder = InlineKeyboardBuilder()
    
    # Добавляем кнопки для каждого сервера
    for server in servers:
        builder.button(
            text=f"{server.name} ({server.country})",
            callback_data=f"server:{server.id}"
        )
    
    # Если у нас есть хотя бы один сервер, добавляем кнопку для возврата к списку кластеров
    if servers and len(servers) > 0:
        cluster_id = servers[0].cluster_id
        builder.button(
            text="◀️ Назад к списку",
            callback_data=f"cluster:{cluster_id}"
        )
    
    # Добавляем кнопку возврата в главное меню
    builder.button(
        text="🏠 Главное меню",
        callback_data="back_to_main"
    )
    
    # Устанавливаем ширину строки в 1 кнопку
    builder.adjust(1)
    
    return builder.as_markup()


def get_admin_server_kb(server: VPNServer) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для управления сервером в админ-панели
    
    Args:
        server: Объект сервера
        
    Returns:
        Инлайн-клавиатура с кнопками управления сервером
    """
    builder = InlineKeyboardBuilder()
    
    # Кнопка включения/выключения сервера
    status_text = "🔴 Выключить" if server.is_active else "🟢 Включить"
    status_action = "disable" if server.is_active else "enable"
    
    builder.button(
        text=status_text,
        callback_data=f"admin_server:{status_action}:{server.id}"
    )
    
    # Кнопка редактирования сервера
    builder.button(
        text="✏️ Редактировать",
        callback_data=f"admin_server:edit:{server.id}"
    )
    
    # Кнопка просмотра статистики
    builder.button(
        text="📊 Статистика",
        callback_data=f"admin_server:stats:{server.id}"
    )
    
    # Кнопка удаления сервера
    builder.button(
        text="🗑️ Удалить",
        callback_data=f"admin_server:delete:{server.id}"
    )
    
    # Кнопка возврата
    builder.button(
        text="◀️ Назад",
        callback_data=f"admin_cluster:{server.cluster_id}"
    )
    
    # Устанавливаем ширину строки в 1 кнопку
    builder.adjust(1)
    
    return builder.as_markup()


def get_admin_cluster_kb(cluster: VPNCluster) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для управления кластером в админ-панели
    
    Args:
        cluster: Объект кластера
        
    Returns:
        Инлайн-клавиатура с кнопками управления кластером
    """
    builder = InlineKeyboardBuilder()
    
    # Кнопка просмотра серверов
    builder.button(
        text="👁️ Просмотр серверов",
        callback_data=f"admin_cluster:view_servers:{cluster.id}"
    )
    
    # Кнопка добавления сервера
    builder.button(
        text="➕ Добавить сервер",
        callback_data=f"admin_cluster:add_server:{cluster.id}"
    )
    
    # Кнопка включения/выключения кластера
    status_text = "🔴 Выключить" if cluster.is_active else "🟢 Включить"
    status_action = "disable" if cluster.is_active else "enable"
    
    builder.button(
        text=status_text,
        callback_data=f"admin_cluster:{status_action}:{cluster.id}"
    )
    
    # Кнопка редактирования кластера
    builder.button(
        text="✏️ Редактировать",
        callback_data=f"admin_cluster:edit:{cluster.id}"
    )
    
    # Кнопка удаления кластера
    builder.button(
        text="🗑️ Удалить",
        callback_data=f"admin_cluster:delete:{cluster.id}"
    )
    
    # Кнопка возврата
    builder.button(
        text="◀️ Назад",
        callback_data="admin:clusters"
    )
    
    # Устанавливаем ширину строки в 1 кнопку
    builder.adjust(1)
    
    return builder.as_markup()


def get_admin_clusters_list_kb(clusters: List[VPNCluster]) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру со списком кластеров для админ-панели
    
    Args:
        clusters: Список объектов кластеров
        
    Returns:
        Инлайн-клавиатура с кнопками выбора кластера
    """
    builder = InlineKeyboardBuilder()
    
    # Добавляем кнопки для каждого кластера
    for cluster in clusters:
        status_emoji = "🟢" if cluster.is_active else "🔴"
        builder.button(
            text=f"{status_emoji} {cluster.name}",
            callback_data=f"admin_cluster:view:{cluster.id}"
        )
    
    # Кнопка добавления нового кластера
    builder.button(
        text="➕ Добавить кластер",
        callback_data="admin_cluster:add"
    )
    
    # Кнопка возврата
    builder.button(
        text="◀️ Назад",
        callback_data="admin:menu"
    )
    
    # Устанавливаем ширину строки в 1 кнопку
    builder.adjust(1)
    
    return builder.as_markup()


def get_admin_servers_list_kb(servers: List[VPNServer], cluster_id: int) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру со списком серверов для админ-панели
    
    Args:
        servers: Список объектов серверов
        cluster_id: ID кластера
        
    Returns:
        Инлайн-клавиатура с кнопками выбора сервера
    """
    builder = InlineKeyboardBuilder()
    
    # Добавляем кнопки для каждого сервера
    for server in servers:
        status_emoji = "🟢" if server.is_active else "🔴"
        builder.button(
            text=f"{status_emoji} {server.name} ({server.country})",
            callback_data=f"admin_server:view:{server.id}"
        )
    
    # Кнопка добавления нового сервера
    builder.button(
        text="➕ Добавить сервер",
        callback_data=f"admin_cluster:add_server:{cluster_id}"
    )
    
    # Кнопка возврата
    builder.button(
        text="◀️ Назад",
        callback_data=f"admin_cluster:view:{cluster_id}"
    )
    
    # Устанавливаем ширину строки в 1 кнопку
    builder.adjust(1)
    
    return builder.as_markup()


def get_server_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для управления серверами"""
    buttons = [
        [
            InlineKeyboardButton(text="➕ Добавить сервер", callback_data="server:add"),
            InlineKeyboardButton(text="📋 Список серверов", callback_data="server:list")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin:menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_server_edit_keyboard(server_id: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру для редактирования сервера"""
    buttons = [
        [
            InlineKeyboardButton(
                text="✏️ Редактировать",
                callback_data=f"server:edit:{server_id}"
            ),
            InlineKeyboardButton(
                text="❌ Удалить",
                callback_data=f"server:delete:{server_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="📊 Статистика",
                callback_data=f"server:stats:{server_id}"
            ),
            InlineKeyboardButton(
                text="🔄 Перезагрузить",
                callback_data=f"server:restart:{server_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="server:list"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons) 