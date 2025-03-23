from typing import Callable, Dict, Any, Awaitable, Union
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramAPIError


class AdminMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Union[Message, CallbackQuery], Dict[str, Any]], Awaitable[Any]],
        event: Union[Message, CallbackQuery],
        data: Dict[str, Any]
    ) -> Any:
        # Получаем пользователя из контекста (установленного AuthMiddleware)
        user = data.get("user")
        
        # Проверяем, является ли пользователь администратором
        if not user or not user.is_admin:
            if isinstance(event, Message):
                await event.answer("⛔ У вас нет доступа к этой команде.")
            elif isinstance(event, CallbackQuery):
                await event.answer("⛔ У вас нет доступа к этому действию.", show_alert=True)
            return
            
        # Если пользователь администратор, продолжаем обработку запроса
        return await handler(event, data) 