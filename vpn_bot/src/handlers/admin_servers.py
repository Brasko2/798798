"""
Обработчики для управления VPN серверами администратором
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging

from ..models.cluster import VPNCluster, VPNServer
from ..models.user import User
from ..exceptions import DatabaseError, VPNServerError
from ..keyboards.server import (
    get_admin_clusters_list_kb, 
    get_admin_servers_list_kb, 
    get_admin_server_kb
)
from ..middlewares.auth import AdminMiddleware

router = Router()
router.message.middleware(AdminMiddleware())
router.callback_query.middleware(AdminMiddleware())

logger = logging.getLogger(__name__)


class ServerForm(StatesGroup):
    """Состояния формы для создания/редактирования сервера"""
    cluster_id = State()  # ID кластера
    name = State()        # Имя сервера
    country = State()     # Страна
    city = State()        # Город
    ip_address = State()  # IP-адрес
    api_url = State()     # URL API
    api_username = State() # Логин API
    api_password = State() # Пароль API
    priority = State()    # Приоритет


@router.callback_query(F.data == "admin:servers")
async def admin_servers_menu(callback: CallbackQuery, user: User):
    """
    Отображает список кластеров для управления серверами
    """
    try:
        # Получаем все кластеры
        clusters = await VPNCluster.get_all()
        
        if not clusters:
            await callback.answer("Нет доступных кластеров. Сначала создайте кластер.", show_alert=True)
            return
            
        text = "🌐 <b>Управление VPN-серверами</b>\n\n"
        text += "Выберите кластер для просмотра и управления его серверами:\n"
        
        # Создаем клавиатуру с кластерами
        keyboard = get_admin_clusters_list_kb(clusters)
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
    
    except Exception as e:
        logger.error(f"Error in admin servers menu: {e}")
        await callback.answer("Ошибка при загрузке списка кластеров", show_alert=True)


@router.callback_query(F.data.startswith("admin_cluster:view_servers:"))
async def admin_view_servers(callback: CallbackQuery, user: User):
    """
    Отображает список серверов выбранного кластера
    """
    try:
        # Извлекаем ID кластера из данных колбэка
        cluster_id = int(callback.data.split(":")[2])
        
        # Получаем информацию о кластере
        cluster = await VPNCluster.get_by_id(cluster_id)
        if not cluster:
            await callback.answer("Выбранный кластер не найден", show_alert=True)
            return
        
        # Получаем серверы кластера
        servers = await VPNServer.get_by_cluster(cluster_id)
        
        text = f"🌐 <b>Серверы кластера {cluster.name}</b>\n\n"
        
        if not servers:
            text += "В этом кластере нет серверов.\n"
            text += "Добавьте первый сервер, нажав кнопку ниже."
        else:
            text += f"Всего серверов: {len(servers)}\n\n"
            text += "Выберите сервер для управления:\n"
        
        # Создаем клавиатуру со списком серверов
        keyboard = get_admin_servers_list_kb(servers, cluster_id)
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
    
    except Exception as e:
        logger.error(f"Error viewing servers in cluster: {e}")
        await callback.answer("Ошибка при загрузке списка серверов", show_alert=True)


@router.callback_query(F.data.startswith("admin_server:view:"))
async def admin_view_server(callback: CallbackQuery, user: User):
    """
    Отображает информацию о выбранном сервере и кнопки управления
    """
    try:
        # Извлекаем ID сервера из данных колбэка
        server_id = int(callback.data.split(":")[2])
        
        # Получаем информацию о сервере
        server = await VPNServer.get_by_id(server_id)
        if not server:
            await callback.answer("Выбранный сервер не найден", show_alert=True)
            return
        
        # Получаем информацию о кластере
        cluster = await VPNCluster.get_by_id(server.cluster_id)
        
        # Получаем нагрузку сервера
        load = await server.get_load()
        
        # Формируем текст сообщения
        text = f"🖥 <b>Сервер: {server.name}</b>\n\n"
        text += f"🆔 ID: <code>{server.id}</code>\n"
        text += f"🌐 Кластер: {cluster.name if cluster else 'Неизвестно'}\n"
        text += f"📍 Местоположение: {server.country}, {server.city}\n"
        text += f"🔄 Статус: {'🟢 Активен' if server.is_active else '🔴 Неактивен'}\n"
        text += f"🔢 Приоритет: {server.priority}\n"
        text += f"💻 IP-адрес: <code>{server.ip_address}</code>\n"
        text += f"🔗 API URL: <code>{server.api_url}</code>\n"
        text += f"👤 API логин: <code>{server.api_username}</code>\n"
        text += f"👥 Активных подписок: {load}\n"
        text += f"📅 Создан: {server.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        text += f"🔄 Обновлён: {server.updated_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        text += "Выберите действие:"
        
        # Создаем клавиатуру управления сервером
        keyboard = get_admin_server_kb(server)
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
    
    except Exception as e:
        logger.error(f"Error viewing server details: {e}")
        await callback.answer("Ошибка при загрузке информации о сервере", show_alert=True)


@router.callback_query(F.data.startswith("admin_server:enable:") | F.data.startswith("admin_server:disable:"))
async def admin_toggle_server_status(callback: CallbackQuery, user: User):
    """
    Включает или отключает сервер
    """
    try:
        # Извлекаем действие и ID сервера из данных колбэка
        action, server_id = callback.data.split(":")[1:3]
        server_id = int(server_id)
        
        # Получаем информацию о сервере
        server = await VPNServer.get_by_id(server_id)
        if not server:
            await callback.answer("Выбранный сервер не найден", show_alert=True)
            return
        
        # Меняем статус сервера
        new_status = action == "enable"
        result = await server.update(is_active=new_status)
        
        if result:
            status_text = "включен" if new_status else "отключен"
            await callback.answer(f"Сервер {server.name} успешно {status_text}")
            
            # Обновляем информацию о сервере
            await admin_view_server(callback, user)
        else:
            await callback.answer("Не удалось изменить статус сервера", show_alert=True)
    
    except Exception as e:
        logger.error(f"Error toggling server status: {e}")
        await callback.answer("Ошибка при изменении статуса сервера", show_alert=True)


@router.callback_query(F.data.startswith("admin_server:delete:"))
async def admin_delete_server(callback: CallbackQuery, user: User):
    """
    Удаляет сервер
    """
    try:
        # Извлекаем ID сервера из данных колбэка
        server_id = int(callback.data.split(":")[2])
        
        # Получаем информацию о сервере
        server = await VPNServer.get_by_id(server_id)
        if not server:
            await callback.answer("Выбранный сервер не найден", show_alert=True)
            return
        
        # Запоминаем ID кластера для возврата
        cluster_id = server.cluster_id
        
        # Удаляем сервер
        result = await server.delete()
        
        if result:
            await callback.answer(f"Сервер {server.name} успешно удален")
            
            # Возвращаемся к списку серверов кластера
            callback.data = f"admin_cluster:view_servers:{cluster_id}"
            await admin_view_servers(callback, user)
        else:
            await callback.answer("Не удалось удалить сервер. Возможно, у него есть активные подписки.", show_alert=True)
    
    except Exception as e:
        logger.error(f"Error deleting server: {e}")
        await callback.answer("Ошибка при удалении сервера", show_alert=True)


@router.callback_query(F.data.startswith("admin_server:stats:"))
async def admin_server_stats(callback: CallbackQuery, user: User):
    """
    Показывает статистику сервера
    """
    try:
        # Извлекаем ID сервера из данных колбэка
        server_id = int(callback.data.split(":")[2])
        
        # Получаем информацию о сервере
        server = await VPNServer.get_by_id(server_id)
        if not server:
            await callback.answer("Выбранный сервер не найден", show_alert=True)
            return
        
        # Получаем статистику по подпискам
        from ..models.subscription import Subscription
        active_subscriptions = await Subscription.get_active_by_server(server_id)
        
        # Формируем статистику
        text = f"📊 <b>Статистика сервера {server.name}</b>\n\n"
        text += f"👥 Активных подписок: {len(active_subscriptions)}\n"
        
        # Группируем подписки по дням до истечения
        expiring_soon = 0
        expired_within_day = 0
        
        for sub in active_subscriptions:
            if sub.days_left <= 3:
                expiring_soon += 1
            if sub.days_left <= 1:
                expired_within_day += 1
        
        text += f"⏳ Истекают в ближайшие 3 дня: {expiring_soon}\n"
        text += f"⚠️ Истекают в течение 24 часов: {expired_within_day}\n\n"
        
        # Тут можно добавить другую статистику, например, по трафику
        
        # Добавляем кнопку назад
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(
            text="◀️ Назад к серверу",
            callback_data=f"admin_server:view:{server_id}"
        )
        keyboard = builder.as_markup()
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
    
    except Exception as e:
        logger.error(f"Error showing server stats: {e}")
        await callback.answer("Ошибка при загрузке статистики сервера", show_alert=True)


@router.callback_query(F.data.startswith("admin_cluster:add_server:"))
async def admin_add_server_start(callback: CallbackQuery, state: FSMContext, user: User):
    """
    Начинает процесс добавления нового сервера
    """
    try:
        # Извлекаем ID кластера из данных колбэка
        cluster_id = int(callback.data.split(":")[2])
        
        # Получаем информацию о кластере
        cluster = await VPNCluster.get_by_id(cluster_id)
        if not cluster:
            await callback.answer("Выбранный кластер не найден", show_alert=True)
            return
        
        # Сохраняем ID кластера в состояние
        await state.update_data(cluster_id=cluster_id)
        
        # Устанавливаем состояние формы
        await state.set_state(ServerForm.name)
        
        text = f"🆕 <b>Добавление нового сервера в кластер {cluster.name}</b>\n\n"
        text += "Введите название сервера:"
        
        # Кнопка отмены
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(
            text="❌ Отмена",
            callback_data=f"admin_cluster:view_servers:{cluster_id}"
        )
        keyboard = builder.as_markup()
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
    
    except Exception as e:
        logger.error(f"Error starting add server process: {e}")
        await callback.answer("Ошибка при добавлении сервера", show_alert=True)


@router.message(ServerForm.name)
async def process_server_name(message: Message, state: FSMContext, user: User):
    """
    Обрабатывает ввод названия сервера
    """
    # Сохраняем название сервера
    await state.update_data(name=message.text)
    
    # Переходим к следующему шагу - ввод страны
    await state.set_state(ServerForm.country)
    
    # Получаем данные из состояния
    data = await state.get_data()
    cluster_id = data["cluster_id"]
    
    # Создаем клавиатуру отмены
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(
        text="❌ Отмена",
        callback_data=f"admin_cluster:view_servers:{cluster_id}"
    )
    keyboard = builder.as_markup()
    
    await message.answer(
        "Введите страну расположения сервера (например, Russia):",
        reply_markup=keyboard
    )


@router.message(ServerForm.country)
async def process_server_country(message: Message, state: FSMContext):
    """
    Обрабатывает ввод страны сервера
    """
    # Сохраняем страну
    await state.update_data(country=message.text)
    
    # Переходим к следующему шагу - ввод города
    await state.set_state(ServerForm.city)
    
    # Получаем данные из состояния
    data = await state.get_data()
    cluster_id = data["cluster_id"]
    
    # Создаем клавиатуру отмены
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(
        text="❌ Отмена",
        callback_data=f"admin_cluster:view_servers:{cluster_id}"
    )
    keyboard = builder.as_markup()
    
    await message.answer(
        "Введите город расположения сервера:",
        reply_markup=keyboard
    )


@router.message(ServerForm.city)
async def process_server_city(message: Message, state: FSMContext):
    """
    Обрабатывает ввод города сервера
    """
    # Сохраняем город
    await state.update_data(city=message.text)
    
    # Переходим к следующему шагу - ввод IP-адреса
    await state.set_state(ServerForm.ip_address)
    
    # Получаем данные из состояния
    data = await state.get_data()
    cluster_id = data["cluster_id"]
    
    # Создаем клавиатуру отмены
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(
        text="❌ Отмена",
        callback_data=f"admin_cluster:view_servers:{cluster_id}"
    )
    keyboard = builder.as_markup()
    
    await message.answer(
        "Введите IP-адрес сервера:",
        reply_markup=keyboard
    )


@router.message(ServerForm.ip_address)
async def process_server_ip(message: Message, state: FSMContext):
    """
    Обрабатывает ввод IP-адреса сервера
    """
    # Сохраняем IP-адрес
    await state.update_data(ip_address=message.text)
    
    # Переходим к следующему шагу - ввод URL API
    await state.set_state(ServerForm.api_url)
    
    # Получаем данные из состояния
    data = await state.get_data()
    cluster_id = data["cluster_id"]
    
    # Создаем клавиатуру отмены
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(
        text="❌ Отмена",
        callback_data=f"admin_cluster:view_servers:{cluster_id}"
    )
    keyboard = builder.as_markup()
    
    await message.answer(
        "Введите URL API сервера (например, http://192.168.1.100:54321):",
        reply_markup=keyboard
    )


@router.message(ServerForm.api_url)
async def process_server_api_url(message: Message, state: FSMContext):
    """
    Обрабатывает ввод URL API сервера
    """
    # Сохраняем URL API
    await state.update_data(api_url=message.text)
    
    # Переходим к следующему шагу - ввод логина API
    await state.set_state(ServerForm.api_username)
    
    # Получаем данные из состояния
    data = await state.get_data()
    cluster_id = data["cluster_id"]
    
    # Создаем клавиатуру отмены
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(
        text="❌ Отмена",
        callback_data=f"admin_cluster:view_servers:{cluster_id}"
    )
    keyboard = builder.as_markup()
    
    await message.answer(
        "Введите логин для API сервера:",
        reply_markup=keyboard
    )


@router.message(ServerForm.api_username)
async def process_server_api_username(message: Message, state: FSMContext):
    """
    Обрабатывает ввод логина API сервера
    """
    # Сохраняем логин API
    await state.update_data(api_username=message.text)
    
    # Переходим к следующему шагу - ввод пароля API
    await state.set_state(ServerForm.api_password)
    
    # Получаем данные из состояния
    data = await state.get_data()
    cluster_id = data["cluster_id"]
    
    # Создаем клавиатуру отмены
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(
        text="❌ Отмена",
        callback_data=f"admin_cluster:view_servers:{cluster_id}"
    )
    keyboard = builder.as_markup()
    
    await message.answer(
        "Введите пароль для API сервера:",
        reply_markup=keyboard
    )


@router.message(ServerForm.api_password)
async def process_server_api_password(message: Message, state: FSMContext):
    """
    Обрабатывает ввод пароля API сервера
    """
    # Сохраняем пароль API
    await state.update_data(api_password=message.text)
    
    # Переходим к следующему шагу - ввод приоритета
    await state.set_state(ServerForm.priority)
    
    # Получаем данные из состояния
    data = await state.get_data()
    cluster_id = data["cluster_id"]
    
    # Создаем клавиатуру отмены
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(
        text="❌ Отмена",
        callback_data=f"admin_cluster:view_servers:{cluster_id}"
    )
    keyboard = builder.as_markup()
    
    await message.answer(
        "Введите приоритет сервера (число от 1 до 10, где 1 - наивысший приоритет):",
        reply_markup=keyboard
    )


@router.message(ServerForm.priority)
async def process_server_priority(message: Message, state: FSMContext):
    """
    Обрабатывает ввод приоритета сервера и завершает создание
    """
    try:
        # Проверяем, что введено число
        try:
            priority = int(message.text)
            if priority < 1 or priority > 10:
                raise ValueError("Приоритет должен быть от 1 до 10")
        except ValueError:
            await message.answer("Пожалуйста, введите число от 1 до 10")
            return
        
        # Сохраняем приоритет
        await state.update_data(priority=priority)
        
        # Получаем все данные из состояния
        data = await state.get_data()
        
        # Создаем новый сервер
        server = await VPNServer.create(
            cluster_id=data["cluster_id"],
            name=data["name"],
            country=data["country"],
            city=data["city"],
            ip_address=data["ip_address"],
            api_url=data["api_url"],
            api_username=data["api_username"],
            api_password=data["api_password"],
            priority=data["priority"]
        )
        
        # Проверяем подключение к серверу
        try:
            # Это необязательный шаг, можно добавить проверку подключения
            pass
        except Exception as e:
            logger.warning(f"Error testing connection to server: {e}")
        
        # Очищаем состояние
        await state.clear()
        
        # Возвращаемся к списку серверов кластера
        text = f"✅ Сервер {server.name} успешно добавлен!\n\n"
        text += f"Кластер: {server.cluster_id}\n"
        text += f"ID: {server.id}\n"
        text += f"Страна: {server.country}\n"
        text += f"Город: {server.city}\n"
        text += f"IP: {server.ip_address}\n"
        text += f"Приоритет: {server.priority}\n\n"
        text += "Возврат к списку серверов..."
        
        # Создаем клавиатуру для возврата
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(
            text="📋 К списку серверов",
            callback_data=f"admin_cluster:view_servers:{server.cluster_id}"
        )
        builder.button(
            text="🖥 Просмотр сервера",
            callback_data=f"admin_server:view:{server.id}"
        )
        keyboard = builder.as_markup()
        
        await message.answer(text, reply_markup=keyboard)
    
    except Exception as e:
        logger.error(f"Error creating server: {e}")
        await message.answer(f"Ошибка при создании сервера: {str(e)}")
        
        # Возвращаемся к списку серверов кластера
        data = await state.get_data()
        cluster_id = data["cluster_id"]
        
        # Создаем клавиатуру для возврата
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(
            text="📋 К списку серверов",
            callback_data=f"admin_cluster:view_servers:{cluster_id}"
        )
        keyboard = builder.as_markup()
        
        await message.answer("Возврат к списку серверов...", reply_markup=keyboard)
        
        # Очищаем состояние
        await state.clear() 