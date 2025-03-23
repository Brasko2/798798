"""
Обработчики административных команд бота
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from ..models import User, Tariff, Subscription, Payment, SupportTicket
from ..keyboards import get_admin_keyboard
from ..exceptions import DatabaseError


logger = logging.getLogger(__name__)
router = Router()


class TariffForm(StatesGroup):
    """Состояния для добавления тарифа"""
    name = State()
    description = State()
    price = State()
    duration = State()
    traffic_limit = State()
    devices = State()


@router.message(Command("admin"))
async def cmd_admin(message: Message, user: User):
    """Обработчик команды /admin - показывает админ-панель"""
    if not user.is_admin:
        await message.answer("⛔ У вас нет доступа к этой команде.")
        return
    
    await message.answer(
        "👑 <b>Панель администратора</b>\n\n"
        "Используйте меню ниже для управления ботом.",
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML"
    )


@router.message(F.text == "📊 Статистика")
async def admin_stats(message: Message, user: User):
    """Обработчик кнопки Статистика - показывает статистику бота"""
    if not user.is_admin:
        return
    
    try:
        # Собираем статистику
        users_count = await User.count()
        active_subscriptions = await Subscription.get_active_count()
        total_payments = await Payment.get_total_amount()
        open_tickets = await SupportTicket.get_open_count()
        
        stats_text = (
            "📊 <b>Статистика бота</b>\n\n"
            f"👥 Пользователей: {users_count}\n"
            f"🔑 Активных подписок: {active_subscriptions}\n"
            f"💰 Общая сумма платежей: {total_payments:.2f} руб.\n"
            f"🆘 Открытых тикетов: {open_tickets}\n"
        )
        
        await message.answer(stats_text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        await message.answer("❌ Ошибка при получении статистики.")


@router.message(F.text == "👥 Пользователи")
async def admin_users(message: Message, user: User):
    """Обработчик кнопки Пользователи - показывает список пользователей"""
    if not user.is_admin:
        return
    
    try:
        # Получаем последних 10 пользователей
        users = await User.get_recent(10)
        
        if not users:
            await message.answer("Пользователей пока нет.")
            return
        
        users_text = "👥 <b>Последние пользователи</b>\n\n"
        
        for idx, u in enumerate(users, 1):
            users_text += (
                f"{idx}. ID: {u.id}\n"
                f"   Имя: {u.full_name}\n"
                f"   Баланс: {u.balance:.2f} руб.\n"
                f"   Создан: {u.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            )
        
        users_text += "Для получения подробной информации о пользователе используйте команду /user_info [ID]"
        
        await message.answer(users_text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error getting users list: {e}")
        await message.answer("❌ Ошибка при получении списка пользователей.")


@router.message(F.text == "💵 Финансы")
async def admin_finances(message: Message, user: User):
    """Обработчик кнопки Финансы - показывает финансовую информацию"""
    if not user.is_admin:
        return
    
    try:
        # Получаем финансовую статистику
        total_payments = await Payment.get_total_amount()
        monthly_payments = await Payment.get_monthly_amount()
        recent_payments = await Payment.get_recent(5)
        
        finance_text = (
            "💵 <b>Финансовая информация</b>\n\n"
            f"💰 Общая сумма платежей: {total_payments:.2f} руб.\n"
            f"📅 Платежи за текущий месяц: {monthly_payments:.2f} руб.\n\n"
            "<b>Последние платежи:</b>\n"
        )
        
        if recent_payments:
            for idx, payment in enumerate(recent_payments, 1):
                finance_text += (
                    f"{idx}. ID: {payment.id}\n"
                    f"   Пользователь: {payment.user_id}\n"
                    f"   Сумма: {payment.amount:.2f} руб.\n"
                    f"   Статус: {payment.status.value}\n"
                    f"   Дата: {payment.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
                )
        else:
            finance_text += "Платежей пока нет.\n"
        
        await message.answer(finance_text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error getting financial information: {e}")
        await message.answer("❌ Ошибка при получении финансовой информации.")


@router.message(F.text == "🔧 Настройки")
async def admin_settings(message: Message, user: User):
    """Обработчик кнопки Настройки - показывает настройки бота"""
    if not user.is_admin:
        return
    
    settings_text = (
        "🔧 <b>Настройки бота</b>\n\n"
        "<b>Доступные команды:</b>\n"
        "/add_tariff - Добавить новый тариф\n"
        "/edit_tariff - Редактировать тариф\n"
        "/delete_tariff - Удалить тариф\n"
        "/list_tariffs - Список всех тарифов\n\n"
        "/broadcast - Отправить сообщение всем пользователям\n"
        "/maintenance - Включить/выключить режим обслуживания\n"
    )
    
    await message.answer(settings_text, parse_mode="HTML")


@router.message(F.text == "🏠 Главное меню")
async def admin_main_menu(message: Message, user: User):
    """Обработчик кнопки возврата в главное меню"""
    from ..keyboards import main_keyboard
    
    await message.answer(
        "Вы вернулись в главное меню.",
        reply_markup=main_keyboard(is_admin=user.is_admin)
    )


@router.message(Command("add_tariff"))
async def cmd_add_tariff(message: Message, user: User, state: FSMContext):
    """Обработчик команды добавления тарифа"""
    if not user.is_admin:
        return
    
    await message.answer(
        "🆕 <b>Добавление нового тарифа</b>\n\n"
        "Введите название тарифа:",
        parse_mode="HTML"
    )
    await state.set_state(TariffForm.name)


@router.message(TariffForm.name)
async def process_tariff_name(message: Message, state: FSMContext):
    """Обработка имени тарифа"""
    await state.update_data(name=message.text)
    await message.answer("Введите описание тарифа:")
    await state.set_state(TariffForm.description)


@router.message(TariffForm.description)
async def process_tariff_description(message: Message, state: FSMContext):
    """Обработка описания тарифа"""
    await state.update_data(description=message.text)
    await message.answer("Введите цену тарифа (в рублях, например 299.99):")
    await state.set_state(TariffForm.price)


@router.message(TariffForm.price)
async def process_tariff_price(message: Message, state: FSMContext):
    """Обработка цены тарифа"""
    try:
        price = float(message.text.replace(",", "."))
        if price <= 0:
            await message.answer("Цена должна быть положительным числом. Попробуйте снова:")
            return
        
        await state.update_data(price=price)
        await message.answer("Введите длительность тарифа (в днях):")
        await state.set_state(TariffForm.duration)
    except ValueError:
        await message.answer("Некорректная цена. Введите число, например 299.99:")


@router.message(TariffForm.duration)
async def process_tariff_duration(message: Message, state: FSMContext):
    """Обработка длительности тарифа"""
    try:
        duration = int(message.text)
        if duration <= 0:
            await message.answer("Длительность должна быть положительным числом. Попробуйте снова:")
            return
        
        await state.update_data(duration=duration)
        await message.answer(
            "Введите лимит трафика в ГБ (или 0 для безлимитного):"
        )
        await state.set_state(TariffForm.traffic_limit)
    except ValueError:
        await message.answer("Некорректная длительность. Введите целое число:")


@router.message(TariffForm.traffic_limit)
async def process_tariff_traffic(message: Message, state: FSMContext):
    """Обработка лимита трафика"""
    try:
        traffic = float(message.text.replace(",", "."))
        if traffic < 0:
            await message.answer("Лимит трафика не может быть отрицательным. Попробуйте снова:")
            return
        
        # 0 означает безлимитный тариф
        traffic_limit = None if traffic == 0 else traffic
        await state.update_data(traffic_limit=traffic_limit)
        await message.answer("Введите количество устройств:")
        await state.set_state(TariffForm.devices)
    except ValueError:
        await message.answer("Некорректный лимит трафика. Введите число:")


@router.message(TariffForm.devices)
async def process_tariff_devices(message: Message, state: FSMContext):
    """Обработка количества устройств и создание тарифа"""
    try:
        devices = int(message.text)
        if devices <= 0:
            await message.answer("Количество устройств должно быть положительным числом. Попробуйте снова:")
            return
        
        # Получаем все данные формы
        form_data = await state.get_data()
        form_data["devices"] = devices
        
        # Создаем новый тариф
        try:
            tariff = await Tariff.create(
                name=form_data["name"],
                description=form_data["description"],
                price=form_data["price"],
                duration=form_data["duration"],
                traffic_limit=form_data["traffic_limit"],
                devices=form_data["devices"]
            )
            
            # Формируем сообщение с информацией о созданном тарифе
            tariff_info = (
                "✅ <b>Тариф успешно создан!</b>\n\n"
                f"ID: {tariff.id}\n"
                f"Название: {tariff.name}\n"
                f"Описание: {tariff.description}\n"
                f"Цена: {tariff.price:.2f} руб.\n"
                f"Длительность: {tariff.duration} дней\n"
                f"Лимит трафика: {'Безлимитный' if tariff.traffic_limit is None else f'{tariff.traffic_limit} ГБ'}\n"
                f"Количество устройств: {tariff.devices}"
            )
            
            await message.answer(tariff_info, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Error creating tariff: {e}")
            await message.answer(f"❌ Ошибка при создании тарифа: {str(e)}")
            
        # Сбрасываем состояние
        await state.clear()
    except ValueError:
        await message.answer("Некорректное количество устройств. Введите целое число:")


@router.message(Command("admin_info"))
async def cmd_admin_info(message: Message, user: User):
    """
    Административная команда для получения статистики по рефералам
    """
    if not user.is_admin:
        return
        
    try:
        # Получаем статистику по пользователям
        users_count = await User.count()
        
        # Получаем топ-10 рефереров
        users = await User.get_all()
        
        # Сортируем по количеству рефералов (в убывающем порядке)
        top_referrers = sorted(users, key=lambda u: u.referral_count, reverse=True)[:10]
        
        # Формируем сообщение
        text = "📊 <b>Статистика по реферальной системе</b>\n\n"
        text += f"👥 Всего пользователей: {users_count}\n\n"
        
        # Статистика по бонусным дням
        total_bonus_days = sum(u.referral_bonus_days for u in users)
        total_referrals = sum(u.referral_count for u in users)
        text += f"🔗 Всего рефералов: {total_referrals}\n"
        text += f"⏳ Всего бонусных дней: {total_bonus_days}\n\n"
        
        # Топ рефереров
        text += "<b>Топ-10 рефереров:</b>\n"
        for i, ref_user in enumerate(top_referrers, 1):
            if ref_user.referral_count > 0:
                username = ref_user.username or f"ID: {ref_user.id}"
                text += f"{i}. @{username}: {ref_user.referral_count} рефералов, {ref_user.referral_bonus_days} бонусных дней\n"
        
        await message.answer(text)
        
    except Exception as e:
        logger.error(f"Error getting referral stats: {e}")
        await message.answer(f"Ошибка при получении статистики: {str(e)}")


@router.message(Command("reset_bonus"))
async def cmd_reset_bonus(message: Message, user: User):
    """
    Административная команда для сброса бонусных дней пользователя
    Формат: /reset_bonus <user_id>
    """
    if not user.is_admin:
        return
        
    # Проверяем, есть ли в сообщении ID пользователя
    command_parts = message.text.split()
    if len(command_parts) != 2:
        await message.answer(
            "Использование: /reset_bonus <user_id>\n"
            "Например: /reset_bonus 123456789"
        )
        return
    
    try:
        # Получаем ID пользователя
        target_user_id = int(command_parts[1])
        
        # Получаем пользователя
        target_user = await User.get_by_id(target_user_id)
        if not target_user:
            await message.answer(f"Пользователь с ID {target_user_id} не найден")
            return
            
        # Сохраняем текущее количество бонусных дней для отчета
        prev_bonus_days = target_user.referral_bonus_days
        
        # Обнуляем бонусные дни
        target_user.referral_bonus_days = 0
        await target_user.save()
        
        await message.answer(
            f"✅ Бонусные дни для пользователя {target_user_id} сброшены.\n"
            f"Было: {prev_bonus_days} дней\n"
            f"Стало: 0 дней"
        )
        
    except ValueError:
        await message.answer("Некорректный ID пользователя. Укажите числовой ID.")
    except Exception as e:
        logger.error(f"Error resetting bonus days: {e}")
        await message.answer(f"Ошибка при сбросе бонусных дней: {str(e)}")


@router.message(Command("add_bonus"))
async def cmd_add_bonus(message: Message, user: User):
    """
    Административная команда для добавления бонусных дней пользователю
    Формат: /add_bonus <user_id> <days>
    """
    if not user.is_admin:
        return
        
    # Проверяем, есть ли в сообщении ID пользователя и количество дней
    command_parts = message.text.split()
    if len(command_parts) != 3:
        await message.answer(
            "Использование: /add_bonus <user_id> <days>\n"
            "Например: /add_bonus 123456789 7"
        )
        return
    
    try:
        # Получаем ID пользователя и количество дней
        target_user_id = int(command_parts[1])
        days_to_add = int(command_parts[2])
        
        if days_to_add <= 0:
            await message.answer("Количество дней должно быть положительным числом")
            return
        
        # Получаем пользователя
        target_user = await User.get_by_id(target_user_id)
        if not target_user:
            await message.answer(f"Пользователь с ID {target_user_id} не найден")
            return
            
        # Сохраняем текущее количество бонусных дней для отчета
        prev_bonus_days = target_user.referral_bonus_days
        
        # Добавляем бонусные дни
        await target_user.add_referral_bonus_days(days_to_add)
        
        await message.answer(
            f"✅ Бонусные дни для пользователя {target_user_id} добавлены.\n"
            f"Было: {prev_bonus_days} дней\n"
            f"Добавлено: {days_to_add} дней\n"
            f"Стало: {target_user.referral_bonus_days} дней"
        )
        
    except ValueError:
        await message.answer("Некорректные параметры. Укажите числовые значения.")
    except Exception as e:
        logger.error(f"Error adding bonus days: {e}")
        await message.answer(f"Ошибка при добавлении бонусных дней: {str(e)}") 