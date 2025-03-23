"""
Обработчики для раздела поддержки
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging
from datetime import datetime

from ..models.user import User
from ..models.ticket import Ticket
from ..models.support import SupportTicket
from ..keyboards.support import get_support_keyboard, get_support_ticket_keyboard, get_callback_keyboard
from ..keyboards.main import get_back_to_main_keyboard
from ..middleware import AuthMiddleware

router = Router()
router.message.middleware(AuthMiddleware())
router.callback_query.middleware(AuthMiddleware())

logger = logging.getLogger(__name__)


class SupportForm(StatesGroup):
    """Состояния для FSM поддержки"""
    waiting_for_message = State()
    waiting_for_rating = State()


@router.message(Command("support"))
@router.message(F.text == "💬 Поддержка")
async def cmd_support(message: Message, user: User):
    """
    Обработчик команды /support и кнопки 'Поддержка'
    Показывает меню поддержки
    """
    try:
        text = "💬 <b>ЦЕНТР ПОДДЕРЖКИ</b>\n\n"
        
        text += "Добро пожаловать в раздел поддержки нашего VPN сервиса!\n\n"
        
        text += "🔹 <b>Часто задаваемые вопросы:</b>\n"
        text += "• Как настроить VPN на моем устройстве?\n"
        text += "• Как продлить подписку?\n"
        text += "• Почему соединение медленное?\n"
        text += "• Что делать при ошибке подключения?\n\n"
        
        text += "🔹 <b>Связь с поддержкой:</b>\n"
        text += "Если вы не нашли ответ на свой вопрос, наша команда поддержки всегда готова помочь!\n\n"
        
        text += "⏱ <b>Время работы поддержки:</b>\n"
        text += "Ежедневно с 9:00 до 21:00 по московскому времени\n"
        text += "Среднее время ответа: 1-2 часа\n\n"
        
        text += "Выберите действие из меню ниже 👇"
        
        await message.answer(
            text,
            reply_markup=get_support_keyboard()
        )
    except Exception as e:
        logger.error(f"Error in support command: {e}")
        await message.answer(
            "Произошла ошибка при загрузке раздела поддержки. "
            "Пожалуйста, попробуйте позже."
        )


@router.callback_query(F.data == "support")
async def on_support_button(callback: CallbackQuery, user: User):
    """
    Обработчик нажатия на кнопку поддержки в других меню
    """
    try:
        await cmd_support(callback.message, user)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error handling support button: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "support:faq")
async def on_faq_button(callback: CallbackQuery, user: User):
    """
    Показывает часто задаваемые вопросы
    """
    try:
        text = "❓ <b>ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ</b>\n\n"
        
        text += "<b>Вопрос:</b> Как настроить VPN на моем устройстве?\n"
        text += "<b>Ответ:</b> Подробные инструкции по настройке для разных устройств доступны в разделе «Инструкции по настройке». Там вы найдете пошаговые руководства для Android, iOS, Windows, macOS, Linux и других устройств.\n\n"
        
        text += "<b>Вопрос:</b> Почему VPN работает медленно?\n"
        text += "<b>Ответ:</b> Скорость VPN может зависеть от нескольких факторов: выбранного сервера, вашего интернет-соединения, загруженности сети. Попробуйте подключиться к другому серверу или использовать проводное подключение вместо Wi-Fi для лучшей скорости.\n\n"
        
        text += "<b>Вопрос:</b> Как продлить мою подписку?\n"
        text += "<b>Ответ:</b> Чтобы продлить подписку, перейдите в раздел «Мой профиль» → «Мои подписки» и выберите активную подписку. Нажмите кнопку «Продлить» и следуйте инструкциям. Вы также можете приобрести новую подписку в разделе «Купить VPN».\n\n"
        
        text += "<b>Вопрос:</b> Что делать, если VPN не подключается?\n"
        text += "<b>Ответ:</b> Если VPN не подключается, попробуйте следующие шаги:\n"
        text += "1. Перезапустите приложение VPN\n"
        text += "2. Проверьте подключение к интернету\n"
        text += "3. Попробуйте другой сервер\n"
        text += "4. Временно отключите антивирус или брандмауэр\n"
        text += "5. Обновите приложение VPN до последней версии\n\n"
        
        text += "<b>Вопрос:</b> Могу ли я использовать VPN на нескольких устройствах?\n"
        text += "<b>Ответ:</b> Да, в зависимости от вашего тарифа. Базовый тариф позволяет подключать до 3 устройств, стандартный - до 5, а премиум - до 10 устройств одновременно.\n\n"
        
        text += "<b>Вопрос:</b> Как получить конфигурационный файл для моего устройства?\n"
        text += "<b>Ответ:</b> Перейдите в раздел «Мой профиль» → «Мои подписки», выберите активную подписку и нажмите «Получить конфигурацию». Затем выберите тип вашего устройства.\n\n"
        
        text += "Если вы не нашли ответ на свой вопрос, создайте обращение в поддержку, и мы с радостью вам поможем!"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_to_main_keyboard()
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error showing FAQ: {e}")
        await callback.answer("Произошла ошибка при загрузке FAQ", show_alert=True)


@router.callback_query(F.data == "support:new_ticket")
async def on_new_ticket_button(callback: CallbackQuery, state: FSMContext, user: User):
    """
    Начинает создание нового обращения в поддержку
    """
    try:
        await state.set_state(SupportForm.waiting_for_message)
        
        text = "📝 <b>СОЗДАНИЕ ОБРАЩЕНИЯ В ПОДДЕРЖКУ</b>\n\n"
        
        text += "Пожалуйста, опишите вашу проблему или вопрос как можно более подробно. Включите следующую информацию:\n\n"
        
        text += "• Тип устройства и операционная система\n"
        text += "• Используемое приложение для VPN\n"
        text += "• Точное описание проблемы\n"
        text += "• Когда возникла проблема\n"
        text += "• Что вы уже пробовали сделать для решения\n\n"
        
        text += "Вы также можете прикрепить скриншот к следующему сообщению, если это поможет объяснить проблему.\n\n"
        
        text += "✏️ <b>Введите ваше сообщение ниже:</b>"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_callback_keyboard("support:cancel")
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error starting new ticket: {e}")
        await state.clear()
        await callback.answer("Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "support:my_tickets")
async def on_my_tickets_button(callback: CallbackQuery, user: User):
    """
    Показывает список обращений пользователя
    """
    try:
        # Получаем обращения пользователя
        tickets = await Ticket.get_by_user_id(user.user_id)
        
        if not tickets:
            await callback.message.edit_text(
                "📋 <b>МОИ ОБРАЩЕНИЯ</b>\n\n"
                "У вас пока нет обращений в поддержку.\n\n"
                "Если у вас возникли вопросы или проблемы, создайте новое обращение, и наша команда поддержки поможет вам.",
                reply_markup=get_support_keyboard()
            )
            await callback.answer()
            return
        
        text = "📋 <b>МОИ ОБРАЩЕНИЯ</b>\n\n"
        
        for i, ticket in enumerate(tickets[:5], 1):  # Показываем последние 5 обращений
            status_emoji = "🟢" if ticket.status == "open" else "🔴" if ticket.status == "closed" else "🟡"
            status_text = "Открыто" if ticket.status == "open" else "Закрыто" if ticket.status == "closed" else "В обработке"
            
            # Форматируем дату создания
            created_at = ticket.created_at.strftime("%d.%m.%Y %H:%M")
            
            text += f"{i}. <b>Обращение #{ticket.ticket_id}</b> {status_emoji}\n"
            text += f"📅 Создано: {created_at}\n"
            text += f"📌 Статус: {status_text}\n"
            text += f"📝 Тема: {ticket.subject[:30]}{'...' if len(ticket.subject) > 30 else ''}\n\n"
        
        text += "Выберите обращение для просмотра или создайте новое."
        
        # Создаем клавиатуру с кнопками для каждого обращения
        ticket_buttons = []
        for ticket in tickets[:5]:
            ticket_buttons.append({
                "text": f"#{ticket.ticket_id} - {ticket.subject[:20]}...",
                "callback_data": f"ticket:{ticket.ticket_id}"
            })
        
        await callback.message.edit_text(
            text,
            reply_markup=get_support_ticket_keyboard(ticket_buttons)
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error showing user tickets: {e}")
        await callback.answer("Произошла ошибка при загрузке обращений", show_alert=True)


@router.callback_query(F.data == "support:cancel")
async def on_cancel_button(callback: CallbackQuery, state: FSMContext):
    """
    Отменяет создание обращения
    """
    try:
        current_state = await state.get_state()
        if current_state:
            await state.clear()
        
        await callback.message.edit_text(
            "❌ Создание обращения отменено. Вы можете вернуться в раздел поддержки или главное меню.",
            reply_markup=get_support_keyboard()
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error canceling ticket creation: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


@router.message(SupportForm.waiting_for_message)
async def process_message(message: Message, state: FSMContext, user: User):
    """
    Обрабатывает сообщение для создания обращения
    """
    try:
        # Сохраняем сообщение пользователя
        message_text = message.text or message.caption or "Без текста"
        
        # Проверяем длину сообщения
        if len(message_text) < 10:
            await message.answer(
                "⚠️ Сообщение слишком короткое. Пожалуйста, опишите вашу проблему более подробно "
                "(минимум 10 символов).",
                reply_markup=get_callback_keyboard("support:cancel")
            )
            return
        
        # Создаем тему из первых слов сообщения
        subject = message_text[:50] + ("..." if len(message_text) > 50 else "")
        
        # Получаем фото, если есть
        photo_id = None
        if message.photo:
            photo_id = message.photo[-1].file_id
        
        # Создаем обращение
        ticket = Ticket(
            user_id=user.user_id,
            username=user.username,
            subject=subject,
            message=message_text,
            photo_id=photo_id,
            status="open",
            created_at=datetime.now()
        )
        
        # Сохраняем обращение в базу данных
        await ticket.save()
        
        # Очищаем состояние
        await state.clear()
        
        # Отправляем подтверждение
        await message.answer(
            f"✅ <b>Обращение #{ticket.ticket_id} успешно создано!</b>\n\n"
            f"Ваше обращение принято в обработку. Наши специалисты свяжутся с вами в ближайшее время.\n\n"
            f"Средняя скорость ответа: 1-2 часа в рабочее время.\n"
            f"Вы получите уведомление, когда на ваше обращение ответят.",
            reply_markup=get_back_to_main_keyboard()
        )
        
        # Отправляем уведомление администраторам
        # Этот код будет реализован отдельно в модуле для администраторов
        logger.info(f"New support ticket #{ticket.ticket_id} created by user {user.user_id}")
        
    except Exception as e:
        logger.error(f"Error creating ticket: {e}")
        await state.clear()
        await message.answer(
            "❌ Произошла ошибка при создании обращения. Пожалуйста, попробуйте позже.",
            reply_markup=get_back_to_main_keyboard()
        )


@router.callback_query(F.data.startswith("ticket:"))
async def on_ticket_selected(callback: CallbackQuery, user: User):
    """
    Показывает детали выбранного обращения
    """
    try:
        ticket_id = callback.data.split(":")[1]
        
        # Получаем обращение
        ticket = await Ticket.get_by_id(ticket_id)
        
        if not ticket or ticket.user_id != user.user_id:
            await callback.answer("Обращение не найдено или у вас нет доступа", show_alert=True)
            return
        
        # Форматируем статус
        status_emoji = "🟢" if ticket.status == "open" else "🔴" if ticket.status == "closed" else "🟡"
        status_text = "Открыто" if ticket.status == "open" else "Закрыто" if ticket.status == "closed" else "В обработке"
        
        # Форматируем даты
        created_at = ticket.created_at.strftime("%d.%m.%Y %H:%M")
        updated_at = ticket.updated_at.strftime("%d.%m.%Y %H:%M") if ticket.updated_at else "Нет обновлений"
        
        text = f"📌 <b>ОБРАЩЕНИЕ #{ticket.ticket_id}</b> {status_emoji}\n\n"
        
        text += f"<b>Тема:</b> {ticket.subject}\n"
        text += f"<b>Статус:</b> {status_text}\n"
        text += f"<b>Создано:</b> {created_at}\n"
        text += f"<b>Обновлено:</b> {updated_at}\n\n"
        
        text += f"<b>Ваше сообщение:</b>\n{ticket.message}\n\n"
        
        if ticket.admin_reply:
            text += f"<b>Ответ поддержки:</b>\n{ticket.admin_reply}\n\n"
        else:
            text += "<i>Ожидается ответ от службы поддержки</i>\n\n"
        
        text += "Вы можете закрыть обращение, если ваш вопрос решен, или вернуться к списку обращений."
        
        # Создаем клавиатуру для обращения
        keyboard = InlineKeyboardBuilder()
        
        if ticket.status == "open":
            keyboard.row(
                InlineKeyboardButton(
                    text="🔄 Обновить",
                    callback_data=f"ticket:refresh:{ticket.ticket_id}"
                ),
                InlineKeyboardButton(
                    text="🔒 Закрыть обращение",
                    callback_data=f"ticket:close:{ticket.ticket_id}"
                )
            )
        
        keyboard.row(
            InlineKeyboardButton(
                text="◀️ Назад к списку",
                callback_data="support:my_tickets"
            )
        )
        
        keyboard.row(
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="main_menu"
            )
        )
        
        # Отправляем сообщение с фото, если есть
        if ticket.photo_id and not ticket.admin_reply:
            await callback.message.delete()
            await callback.message.answer_photo(
                photo=ticket.photo_id,
                caption=text,
                reply_markup=keyboard.as_markup()
            )
        else:
            await callback.message.edit_text(
                text,
                reply_markup=keyboard.as_markup()
            )
        
        await callback.answer()
    except Exception as e:
        logger.error(f"Error showing ticket details: {e}")
        await callback.answer("Произошла ошибка при загрузке деталей обращения", show_alert=True)


@router.callback_query(F.data.startswith("ticket:close:"))
async def on_close_ticket(callback: CallbackQuery, user: User):
    """
    Закрывает обращение
    """
    try:
        ticket_id = callback.data.split(":")[-1]
        
        # Получаем обращение
        ticket = await Ticket.get_by_id(ticket_id)
        
        if not ticket or ticket.user_id != user.user_id:
            await callback.answer("Обращение не найдено или у вас нет доступа", show_alert=True)
            return
        
        # Закрываем обращение
        ticket.status = "closed"
        ticket.updated_at = datetime.now()
        await ticket.save()
        
        await callback.message.edit_text(
            f"✅ <b>Обращение #{ticket.ticket_id} закрыто</b>\n\n"
            f"Если у вас возникнут новые вопросы, вы всегда можете создать новое обращение.",
            reply_markup=get_support_keyboard()
        )
        
        await callback.answer("Обращение успешно закрыто")
    except Exception as e:
        logger.error(f"Error closing ticket: {e}")
        await callback.answer("Произошла ошибка при закрытии обращения", show_alert=True)


@router.callback_query(F.data.startswith("ticket:refresh:"))
async def on_refresh_ticket(callback: CallbackQuery, user: User):
    """
    Обновляет информацию об обращении
    """
    try:
        ticket_id = callback.data.split(":")[-1]
        
        # Перенаправляем на просмотр обращения для обновления данных
        callback.data = f"ticket:{ticket_id}"
        await on_ticket_selected(callback, user)
    except Exception as e:
        logger.error(f"Error refreshing ticket: {e}")
        await callback.answer("Произошла ошибка при обновлении информации", show_alert=True) 