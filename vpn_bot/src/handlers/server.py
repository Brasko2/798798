"""
Обработчики для взаимодействия пользователя с VPN серверами
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import logging

from ..models.cluster import VPNCluster, VPNServer, get_optimal_server
from ..models.subscription import Subscription
from ..models.user import User
from ..exceptions import DatabaseError, VPNServerError
from ..keyboards.server import get_server_selection_kb, get_cluster_selection_kb
from ..middleware import AuthMiddleware

router = Router()
router.message.middleware(AuthMiddleware())
router.callback_query.middleware(AuthMiddleware())

logger = logging.getLogger(__name__)


@router.message(Command("servers"))
async def cmd_servers(message: Message, user: User):
    """
    Показывает список доступных серверов и кластеров
    """
    try:
        # Получение всех активных кластеров
        clusters = await VPNCluster.get_all_active()
        
        if not clusters:
            await message.answer("В данный момент нет доступных серверов. Пожалуйста, попробуйте позднее.")
            return
        
        text = "🌐 <b>Доступные VPN-серверы</b>\n\n"
        
        for cluster in clusters:
            # Получаем серверы из кластера
            servers = await VPNServer.get_by_cluster(cluster.id)
            active_servers = [server for server in servers if server.is_active]
            
            if not active_servers:
                continue
                
            text += f"<b>{cluster.name}</b> - {cluster.description}\n"
            text += f"Серверов: {len(active_servers)}\n\n"
            
            # Добавляем информацию о нескольких серверах (не более 3)
            for i, server in enumerate(active_servers[:3]):
                text += f"• {server.name} ({server.country}, {server.city})\n"
            
            if len(active_servers) > 3:
                text += f"... и ещё {len(active_servers) - 3} серверов\n"
            
            text += "\n"
        
        text += "Выберите кластер для просмотра серверов:"
        
        # Клавиатура с кнопками выбора кластера
        keyboard = get_cluster_selection_kb(clusters)
        
        await message.answer(text, reply_markup=keyboard)
    
    except Exception as e:
        logger.error(f"Error listing servers: {e}")
        await message.answer("Произошла ошибка при получении списка серверов. Пожалуйста, попробуйте позднее.")


@router.callback_query(F.data.startswith("cluster:"))
async def on_cluster_selected(callback: CallbackQuery, user: User):
    """
    Обрабатывает выбор кластера и показывает список серверов
    """
    try:
        # Извлекаем ID кластера из данных колбэка
        cluster_id = int(callback.data.split(":")[1])
        
        # Получаем информацию о кластере
        cluster = await VPNCluster.get_by_id(cluster_id)
        if not cluster:
            await callback.answer("Выбранный кластер не найден", show_alert=True)
            return
        
        # Получаем серверы из кластера
        servers = await VPNServer.get_by_cluster(cluster.id)
        active_servers = [server for server in servers if server.is_active]
        
        if not active_servers:
            await callback.answer("В выбранном кластере нет доступных серверов", show_alert=True)
            return
            
        # Формируем текст сообщения
        text = f"🌐 <b>{cluster.name}</b>\n"
        text += f"{cluster.description}\n\n"
        text += f"<b>Доступные серверы ({len(active_servers)}):</b>\n\n"
        
        for i, server in enumerate(active_servers):
            text += f"{i+1}. <b>{server.name}</b>\n"
            text += f"   📍 {server.country}, {server.city}\n"
        
        text += "\nВыберите сервер для подробной информации:"
        
        # Клавиатура с кнопками выбора сервера
        keyboard = get_server_selection_kb(active_servers)
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
    
    except Exception as e:
        logger.error(f"Error displaying servers in cluster: {e}")
        await callback.answer("Произошла ошибка при получении списка серверов", show_alert=True)


@router.callback_query(F.data.startswith("server:"))
async def on_server_selected(callback: CallbackQuery, user: User):
    """
    Обрабатывает выбор сервера и показывает подробную информацию
    """
    try:
        # Извлекаем ID сервера из данных колбэка
        server_id = int(callback.data.split(":")[1])
        
        # Получаем информацию о сервере
        server = await VPNServer.get_by_id(server_id)
        if not server:
            await callback.answer("Выбранный сервер не найден", show_alert=True)
            return
        
        # Получаем информацию о кластере
        cluster = await VPNCluster.get_by_id(server.cluster_id)
        if not cluster:
            cluster_name = "Неизвестный кластер"
        else:
            cluster_name = cluster.name
        
        # Формируем текст сообщения
        text = f"🖥 <b>Сервер: {server.name}</b>\n\n"
        text += f"🌐 Кластер: {cluster_name}\n"
        text += f"📍 Местоположение: {server.country}, {server.city}\n"
        text += f"🔄 Статус: {'🟢 Активен' if server.is_active else '🔴 Неактивен'}\n"
        
        # Получаем активные подписки на этом сервере
        active_subscriptions = await Subscription.get_active_by_server(server_id)
        text += f"👥 Пользователей: {len(active_subscriptions)}\n\n"
        
        # Проверяем, есть ли у пользователя активная подписка на этом сервере
        user_subscriptions = await Subscription.get_active_by_user(user.id)
        user_has_subscription_on_server = any(sub.server_id == server_id for sub in user_subscriptions)
        
        if user_has_subscription_on_server:
            text += "✅ У вас есть активная подписка на этом сервере.\n"
            text += "Используйте команду /subscriptions для просмотра ваших подписок."
        else:
            text += "❌ У вас нет активной подписки на этом сервере.\n"
            text += "Используйте команду /buy для покупки подписки."
        
        # Кнопка "Назад к кластеру"
        keyboard = get_cluster_selection_kb([cluster]) if cluster else None
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
    
    except Exception as e:
        logger.error(f"Error displaying server details: {e}")
        await callback.answer("Произошла ошибка при получении информации о сервере", show_alert=True)


async def select_optimal_server(user_id: int, tariff_id: int) -> VPNServer:
    """
    Выбирает оптимальный сервер для нового пользователя
    
    Args:
        user_id: ID пользователя
        tariff_id: ID тарифа
        
    Returns:
        Объект сервера или None, если нет доступных серверов
    """
    try:
        # Используем функцию выбора оптимального сервера
        return await get_optimal_server()
    except Exception as e:
        logger.error(f"Error selecting optimal server for user {user_id}: {e}")
        raise VPNServerError(f"Failed to select optimal server: {e}") 