from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
import logging

from ..database.models import User
from ..keyboards import get_main_keyboard
from ..middleware import AuthMiddleware

router = Router()
router.message.middleware(AuthMiddleware())
router.callback_query.middleware(AuthMiddleware())

logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message, user: User):
    """Обработчик команды /start с улучшенным дизайном"""
    # Получаем или создаем пользователя в базе данных
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    # Проверяем, является ли пользователь администратором (по id)
    is_admin = user_id in [12345678]  # Добавьте сюда ID администраторов
    
    user = await User.get_or_create(
        id=user_id,
        defaults={
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "is_admin": is_admin,
            "balance": 0,
        }
    )
    
    # Проверяем, использовал ли пользователь пробный период
    has_trial_available = not user.has_used_trial
    
    # Формируем приветственное сообщение с улучшенным дизайном
    text = f"<b>🌟 Привет, {first_name}!</b>\n\n"
    text += "<b>Добро пожаловать в Premier VPN</b> - ваш ключ к безопасному и свободному интернету!\n\n"
    
    # Если пробный период доступен, добавляем информацию о нем
    if has_trial_available:
        text += "🎁 <b>ПОДАРОК ДЛЯ ВАС!</b>\n"
        text += "Активируйте <b>7 дней бесплатного VPN</b> премиум-качества!\n"
        text += "👉 Введите команду /trial для мгновенной активации\n\n"
    
    text += "🛡️ <b>С НАШИМ VPN ВЫ ПОЛУЧАЕТЕ:</b>\n\n"
    text += "✅ <b>Полную анонимность</b> в сети\n"
    text += "✅ <b>Сверхскоростное соединение</b> без ограничений\n"
    text += "✅ <b>Доступ к любым сайтам</b> и сервисам\n"
    text += "✅ <b>Защиту данных</b> по военным стандартам\n"
    text += "✅ <b>Круглосуточную поддержку</b> 24/7\n\n"
    
    # Добавляем информацию о реферальной программе
    text += "👥 <b>ВЫГОДНАЯ РЕФЕРАЛЬНАЯ ПРОГРАММА:</b>\n"
    text += "Приглашайте друзей и получайте до <b>30 дней</b> бесплатного VPN!\n"
    text += "Используйте команду /referral для получения вашей персональной ссылки\n\n"
    
    text += "🚀 <b>НАЧНИТЕ ПРЯМО СЕЙЧАС!</b>\n"
    text += "Используйте кнопки меню для навигации по боту."
    
    # Отправляем приветственное сообщение с основной клавиатурой
    await message.answer(
        text,
        reply_markup=get_main_keyboard(is_admin=user.is_admin)
    )
    logger.info(f"User {user.id} started the bot")


@router.message(F.text == "ℹ️ О сервисе")
async def cmd_about(message: Message):
    """Обработчик кнопки 'О сервисе'"""
    about_text = (
        "ℹ️ <b>О нашем VPN сервисе</b>\n\n"
        "🔒 <b>Надежная защита</b>\n"
        "Мы используем протокол V2Ray, который обеспечивает высокий уровень безопасности "
        "и обходит большинство блокировок.\n\n"
        "⚡ <b>Высокая скорость</b>\n"
        "Наши серверы расположены в оптимальных геолокациях, что обеспечивает "
        "минимальные задержки и высокую скорость соединения.\n\n"
        "💻 <b>Поддержка всех устройств</b>\n"
        "Наш VPN работает на всех популярных платформах: Windows, macOS, Android, iOS.\n\n"
        "🛡️ <b>Политика конфиденциальности</b>\n"
        "Мы не храним логи вашей активности и не передаем ваши данные третьим лицам.\n\n"
        "❓ Если у вас возникли вопросы или трудности, обратитесь в нашу службу поддержки."
    )
    
    await message.answer(
        about_text,
        parse_mode="HTML"
    )


@router.message(F.text == "🏠 Главное меню")
async def cmd_main_menu(message: Message):
    """Обработчик кнопки 'Главное меню'"""
    user_id = message.from_user.id
    user = await User.get(id=user_id)
    
    await message.answer(
        "Вы вернулись в главное меню.",
        reply_markup=get_main_keyboard(is_admin=user.is_admin)
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = (
        "🆘 <b>Список доступных команд:</b>\n\n"
        "/start - Запустить бота\n"
        "/help - Показать это сообщение\n"
        "/profile - Информация о профиле\n"
        "/subscriptions - Мои подписки\n"
        "/buy - Купить VPN\n"
        "/instruction - Инструкции по настройке\n"
        "/support - Обратиться в службу поддержки"
    )
    
    await message.answer(help_text, parse_mode="HTML")


@router.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, user: User):
    """
    Обработчик кнопки "Назад в главное меню"
    """
    # Имитируем команду /start
    await cmd_start(callback.message, user)
    await callback.answer()


@router.message(F.text == "🔗 Реферальная программа")
async def cmd_referral_button(message: Message, user: User):
    """Обработчик кнопки 'Реферальная программа'"""
    # Перенаправляем на основной обработчик реферальной системы
    from .referral import cmd_referral 
    await cmd_referral(message, user) 