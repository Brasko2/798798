"""
Обработчики для инструкций по настройке VPN на разных устройствах
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import logging

from ..models.user import User
from ..keyboards.instructions import get_instructions_keyboard, get_instructions_back_keyboard
from ..middleware import AuthMiddleware

router = Router()
router.message.middleware(AuthMiddleware())
router.callback_query.middleware(AuthMiddleware())

logger = logging.getLogger(__name__)


@router.message(Command("instructions"))
@router.message(F.text == "📲 Инструкции по настройке")
async def cmd_instructions(message: Message, user: User):
    """
    Обработчик команды /instructions и кнопки 'Инструкции по настройке'
    Показывает список доступных инструкций по платформам
    """
    try:
        text = "📲 <b>ИНСТРУКЦИИ ПО НАСТРОЙКЕ VPN</b>\n\n"
        text += "Выберите вашу платформу для получения подробной инструкции по настройке:\n\n"
        text += "📱 <b>Мобильные устройства:</b>\n"
        text += "• Android - настройка VPN через официальное приложение\n"
        text += "• iOS (iPhone/iPad) - безопасное соединение для Apple устройств\n\n"
        
        text += "💻 <b>Компьютеры и ноутбуки:</b>\n"
        text += "• Windows - простая настройка для всех версий Windows\n"
        text += "• macOS - оптимизированное соединение для Mac\n"
        text += "• Linux - подробная инструкция для пользователей Linux\n\n"
        
        text += "🌐 <b>Другие устройства:</b>\n"
        text += "• Роутеры - настройка VPN на уровне маршрутизатора\n"
        text += "• Smart TV - защищенный доступ для телевизоров\n\n"
        
        text += "Выберите платформу из списка ниже 👇"
        
        await message.answer(
            text,
            reply_markup=get_instructions_keyboard()
        )
    except Exception as e:
        logger.error(f"Error in instructions command: {e}")
        await message.answer(
            "Произошла ошибка при получении инструкций. "
            "Пожалуйста, попробуйте позже или обратитесь в поддержку /support"
        )


@router.callback_query(F.data == "instructions")
async def on_instructions_button(callback: CallbackQuery, user: User):
    """
    Обработчик нажатия на кнопку инструкций в других меню
    """
    try:
        await cmd_instructions(callback.message, user)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error handling instructions button: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("instruction:"))
async def on_platform_selected(callback: CallbackQuery, user: User):
    """
    Обработчик выбора платформы для инструкции
    """
    try:
        platform = callback.data.split(":")[1]
        
        # Обрабатываем выбор платформы
        if platform == "android":
            await show_android_instructions(callback)
        elif platform == "ios":
            await show_ios_instructions(callback)
        elif platform == "windows":
            await show_windows_instructions(callback)
        elif platform == "macos":
            await show_macos_instructions(callback)
        elif platform == "linux":
            await show_linux_instructions(callback)
        elif platform == "router":
            await show_router_instructions(callback)
        elif platform == "smarttv":
            await show_smarttv_instructions(callback)
        else:
            await callback.answer("Инструкция находится в разработке", show_alert=True)
        
    except Exception as e:
        logger.error(f"Error showing instructions: {e}")
        await callback.answer("Произошла ошибка при загрузке инструкции", show_alert=True)


async def show_android_instructions(callback: CallbackQuery):
    """
    Показывает инструкцию по настройке VPN на Android
    """
    text = "📱 <b>НАСТРОЙКА VPN НА ANDROID</b>\n\n"
    
    text += "<b>Шаг 1:</b> Установка приложения\n"
    text += "1. Откройте Google Play Store\n"
    text += "2. Найдите и установите приложение «V2rayNG»\n"
    text += "3. Дождитесь завершения установки\n\n"
    
    text += "<b>Шаг 2:</b> Настройка соединения\n"
    text += "1. Откройте приложение V2rayNG\n"
    text += "2. Нажмите на значок «+» в правом нижнем углу\n"
    text += "3. Выберите «Импорт конфигурации из буфера обмена»\n"
    text += "4. Вставьте полученный от бота конфигурационный код\n"
    text += "5. Нажмите «ОК» для сохранения\n\n"
    
    text += "<b>Шаг 3:</b> Подключение\n"
    text += "1. В главном меню приложения выберите добавленный сервер\n"
    text += "2. Нажмите на кнопку «V» внизу экрана для подключения\n"
    text += "3. Подтвердите запрос на создание VPN-соединения\n\n"
    
    text += "<b>Проверка соединения:</b>\n"
    text += "Откройте браузер и перейдите на сайт 2ip.ru для проверки вашего IP-адреса\n\n"
    
    text += "<b>Решение проблем:</b>\n"
    text += "• Если соединение не устанавливается, перезапустите приложение\n"
    text += "• Убедитесь, что разрешили приложению создавать VPN-подключения\n"
    text += "• Попробуйте подключиться через мобильный интернет, если используете Wi-Fi\n\n"
    
    text += "Видео-инструкция: <a href='https://youtu.be/example'>Смотреть на YouTube</a>"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_instructions_back_keyboard('android'),
        disable_web_page_preview=True
    )
    await callback.answer()


async def show_ios_instructions(callback: CallbackQuery):
    """
    Показывает инструкцию по настройке VPN на iOS
    """
    text = "📱 <b>НАСТРОЙКА VPN НА iPHONE/iPAD</b>\n\n"
    
    text += "<b>Шаг 1:</b> Установка приложения\n"
    text += "1. Откройте App Store\n"
    text += "2. Найдите и установите приложение «Shadowrocket»\n"
    text += "   (приложение платное, цена около 199 руб.)\n"
    text += "3. Дождитесь завершения установки\n\n"
    
    text += "<b>Шаг 2:</b> Настройка соединения\n"
    text += "1. Откройте раздел «Мои подписки» в нашем боте\n"
    text += "2. Выберите активную подписку и нажмите «Получить конфигурацию»\n"
    text += "3. Выберите «iOS» и скопируйте ссылку\n"
    text += "4. Запустите Shadowrocket\n"
    text += "5. Приложение автоматически распознает ссылку и предложит добавить конфигурацию\n"
    text += "6. Нажмите «Добавить» для сохранения\n\n"
    
    text += "<b>Шаг 3:</b> Подключение\n"
    text += "1. В главном меню приложения выберите добавленный сервер\n"
    text += "2. Включите переключатель для активации VPN\n"
    text += "3. Подтвердите запрос на создание VPN-соединения\n\n"
    
    text += "<b>Проверка соединения:</b>\n"
    text += "Откройте браузер Safari и перейдите на сайт 2ip.ru для проверки вашего IP-адреса\n\n"
    
    text += "<b>Решение проблем:</b>\n"
    text += "• Если соединение не устанавливается, перезапустите приложение\n"
    text += "• Проверьте наличие подключения к интернету\n"
    text += "• Попробуйте другой сервер из списка, если доступно несколько\n\n"
    
    text += "Видео-инструкция: <a href='https://youtu.be/example'>Смотреть на YouTube</a>"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_instructions_back_keyboard('ios'),
        disable_web_page_preview=True
    )
    await callback.answer()


async def show_windows_instructions(callback: CallbackQuery):
    """
    Показывает инструкцию по настройке VPN на Windows
    """
    text = "💻 <b>НАСТРОЙКА VPN НА WINDOWS</b>\n\n"
    
    text += "<b>Шаг 1:</b> Установка программы\n"
    text += "1. Скачайте программу V2rayN по ссылке: <a href='https://github.com/2dust/v2rayN/releases'>Скачать V2rayN</a>\n"
    text += "2. Распакуйте архив в удобное место на компьютере\n"
    text += "3. Запустите файл v2rayN.exe\n\n"
    
    text += "<b>Шаг 2:</b> Настройка соединения\n"
    text += "1. Откройте раздел «Мои подписки» в нашем боте\n"
    text += "2. Выберите активную подписку и нажмите «Получить конфигурацию»\n"
    text += "3. Выберите «Windows» и скопируйте код\n"
    text += "4. В программе V2rayN нажмите на кнопку «Servers» в верхнем меню\n"
    text += "5. Выберите «Import from clipboard»\n"
    text += "6. Программа автоматически добавит новый сервер в список\n\n"
    
    text += "<b>Шаг 3:</b> Подключение\n"
    text += "1. Правой кнопкой мыши нажмите на добавленный сервер\n"
    text += "2. Выберите «Set as active server»\n"
    text += "3. В трее (правый нижний угол экрана) найдите иконку V2rayN\n"
    text += "4. Нажмите правой кнопкой мыши на иконку и выберите «Enable V2ray routing»\n\n"
    
    text += "<b>Проверка соединения:</b>\n"
    text += "Откройте браузер и перейдите на сайт 2ip.ru для проверки вашего IP-адреса\n\n"
    
    text += "<b>Решение проблем:</b>\n"
    text += "• Если программа не запускается, установите .NET Framework\n"
    text += "• При проблемах с подключением проверьте брандмауэр Windows\n"
    text += "• Если соединение медленное, попробуйте другой протокол в настройках\n\n"
    
    text += "Видео-инструкция: <a href='https://youtu.be/example'>Смотреть на YouTube</a>"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_instructions_back_keyboard('windows'),
        disable_web_page_preview=True
    )
    await callback.answer()


async def show_macos_instructions(callback: CallbackQuery):
    """
    Показывает инструкцию по настройке VPN на macOS
    """
    text = "🍏 <b>НАСТРОЙКА VPN НА macOS</b>\n\n"
    
    text += "<b>Шаг 1:</b> Установка программы\n"
    text += "1. Скачайте программу V2rayU по ссылке: <a href='https://github.com/yanue/V2rayU/releases'>Скачать V2rayU</a>\n"
    text += "2. Откройте скачанный .dmg файл и перетащите программу в папку Applications\n"
    text += "3. При первом запуске нажмите правой кнопкой мыши на иконку программы и выберите «Открыть»\n\n"
    
    text += "<b>Шаг 2:</b> Настройка соединения\n"
    text += "1. Откройте раздел «Мои подписки» в нашем боте\n"
    text += "2. Выберите активную подписку и нажмите «Получить конфигурацию»\n"
    text += "3. Выберите «macOS» и скопируйте код\n"
    text += "4. Нажмите на иконку V2rayU в строке меню (верхняя панель)\n"
    text += "5. Выберите «Import from clipboard»\n"
    text += "6. Программа автоматически добавит новый сервер\n\n"
    
    text += "<b>Шаг 3:</b> Подключение\n"
    text += "1. Нажмите на иконку V2rayU в строке меню\n"
    text += "2. Выберите добавленный сервер из списка серверов\n"
    text += "3. Нажмите «Turn V2ray-Core On» для подключения\n"
    text += "4. При запросе введите пароль администратора macOS\n\n"
    
    text += "<b>Проверка соединения:</b>\n"
    text += "Откройте браузер и перейдите на сайт 2ip.ru для проверки вашего IP-адреса\n\n"
    
    text += "<b>Решение проблем:</b>\n"
    text += "• Если программа блокируется системой, откройте Системные настройки → Безопасность и конфиденциальность и разрешите запуск\n"
    text += "• При проблемах с запуском удалите приложение и установите заново\n"
    text += "• Для улучшения скорости попробуйте другие настройки прокси в меню программы\n\n"
    
    text += "Видео-инструкция: <a href='https://youtu.be/example'>Смотреть на YouTube</a>"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_instructions_back_keyboard('macos'),
        disable_web_page_preview=True
    )
    await callback.answer()


async def show_linux_instructions(callback: CallbackQuery):
    """
    Показывает инструкцию по настройке VPN на Linux
    """
    text = "🐧 <b>НАСТРОЙКА VPN НА LINUX</b>\n\n"
    
    text += "<b>Шаг 1:</b> Установка программы\n"
    text += "1. Откройте терминал (Ctrl+Alt+T в большинстве дистрибутивов)\n"
    text += "2. Установите V2ray Core с помощью следующей команды:\n"
    text += "<code>curl -L -s https://install.direct/go.sh | sudo bash</code>\n"
    text += "3. Установите Qv2ray (графический интерфейс):\n"
    text += "<code>sudo apt install qv2ray</code> (для Debian/Ubuntu)\n"
    text += "<code>sudo pacman -S qv2ray</code> (для Arch Linux)\n\n"
    
    text += "<b>Шаг 2:</b> Настройка соединения\n"
    text += "1. Откройте раздел «Мои подписки» в нашем боте\n"
    text += "2. Выберите активную подписку и нажмите «Получить конфигурацию»\n"
    text += "3. Выберите «Linux» и скопируйте код\n"
    text += "4. Запустите Qv2ray из меню приложений\n"
    text += "5. Нажмите на кнопку «Импорт» и выберите «Импорт из буфера обмена»\n"
    text += "6. Программа автоматически добавит новый сервер\n\n"
    
    text += "<b>Шаг 3:</b> Подключение\n"
    text += "1. В главном окне Qv2ray выберите добавленный сервер\n"
    text += "2. Нажмите правой кнопкой мыши и выберите «Подключиться к этому»\n"
    text += "3. Индикатор рядом с сервером станет зеленым при успешном подключении\n\n"
    
    text += "<b>Настройка для командной строки (альтернативный метод):</b>\n"
    text += "1. Создайте файл конфигурации:\n"
    text += "<code>sudo nano /etc/v2ray/config.json</code>\n"
    text += "2. Вставьте скопированный конфигурационный код\n"
    text += "3. Нажмите Ctrl+O, затем Enter для сохранения, и Ctrl+X для выхода\n"
    text += "4. Запустите сервис V2ray:\n"
    text += "<code>sudo systemctl start v2ray</code>\n"
    text += "5. Для автозапуска при загрузке:\n"
    text += "<code>sudo systemctl enable v2ray</code>\n\n"
    
    text += "<b>Проверка соединения:</b>\n"
    text += "Выполните в терминале:\n"
    text += "<code>curl ifconfig.me</code>\n\n"
    
    text += "<b>Решение проблем:</b>\n"
    text += "• Проверьте статус сервиса: <code>sudo systemctl status v2ray</code>\n"
    text += "• Просмотрите логи: <code>sudo journalctl -u v2ray</code>\n"
    text += "• Если IP не меняется, проверьте настройки прокси в программе\n\n"
    
    text += "Для более подробных инструкций обратитесь в нашу службу поддержки."
    
    await callback.message.edit_text(
        text,
        reply_markup=get_instructions_back_keyboard('linux'),
        disable_web_page_preview=True
    )
    await callback.answer()


async def show_router_instructions(callback: CallbackQuery):
    """
    Показывает инструкцию по настройке VPN на роутере
    """
    text = "🌐 <b>НАСТРОЙКА VPN НА РОУТЕРЕ</b>\n\n"
    
    text += "⚠️ <b>Важное примечание:</b>\n"
    text += "Настройка VPN на роутере позволяет защитить все устройства в вашей сети, но требует продвинутых навыков и зависит от модели роутера. Ниже приведены общие инструкции.\n\n"
    
    text += "<b>Поддерживаемые роутеры:</b>\n"
    text += "• AsusWRT (официальная прошивка для Asus)\n"
    text += "• OpenWRT (открытая прошивка для многих моделей)\n"
    text += "• DD-WRT (альтернативная прошивка)\n"
    text += "• Роутеры с поддержкой Merlin или Padavan\n\n"
    
    text += "<b>Общие шаги по настройке:</b>\n\n"
    
    text += "<b>1. Подготовка роутера</b>\n"
    text += "• Убедитесь, что ваш роутер поддерживает установку VPN-клиентов\n"
    text += "• Возможно, потребуется обновить прошивку или установить альтернативную\n"
    text += "• Сделайте резервную копию настроек роутера перед внесением изменений\n\n"
    
    text += "<b>2. Получение конфигурации</b>\n"
    text += "• Откройте раздел «Мои подписки» в нашем боте\n"
    text += "• Выберите активную подписку и нажмите «Получить конфигурацию»\n"
    text += "• Выберите «Router» и скопируйте код\n\n"
    
    text += "<b>3. Настройка на роутере Asus (как пример)</b>\n"
    text += "• Войдите в веб-интерфейс роутера (обычно http://192.168.1.1 или http://router.asus.com)\n"
    text += "• Перейдите в раздел VPN → VPN Client\n"
    text += "• Выберите тип VPN: OpenVPN или WireGuard (в зависимости от поддержки)\n"
    text += "• Вставьте скопированную конфигурацию или загрузите файл настроек\n"
    text += "• Сохраните настройки и активируйте VPN-соединение\n\n"
    
    text += "<b>4. Маршрутизация трафика</b>\n"
    text += "• Вы можете настроить выборочную маршрутизацию для отдельных устройств\n"
    text += "• Или направить весь трафик сети через VPN\n\n"
    
    text += "<b>Проверка соединения:</b>\n"
    text += "• Подключите устройство к вашей WiFi сети\n"
    text += "• Откройте браузер и перейдите на сайт 2ip.ru для проверки IP-адреса\n\n"
    
    text += "⚠️ <b>Внимание:</b> Из-за сложности и разнообразия моделей роутеров мы рекомендуем обратиться в нашу службу поддержки для получения подробных инструкций для вашей конкретной модели."
    
    await callback.message.edit_text(
        text,
        reply_markup=get_instructions_back_keyboard('router'),
        disable_web_page_preview=True
    )
    await callback.answer()


async def show_smarttv_instructions(callback: CallbackQuery):
    """
    Показывает инструкцию по настройке VPN на Smart TV
    """
    text = "📺 <b>НАСТРОЙКА VPN НА SMART TV</b>\n\n"
    
    text += "⚠️ <b>Важное примечание:</b>\n"
    text += "Настройка VPN на Smart TV зависит от операционной системы телевизора (Android TV, Samsung Tizen, LG WebOS и т.д.). Ниже приведены инструкции для наиболее распространенных систем.\n\n"
    
    text += "<b>Метод 1: Для Smart TV на Android TV</b>\n\n"
    
    text += "<b>Шаг 1:</b> Установка приложения\n"
    text += "1. Откройте Google Play Store на вашем телевизоре\n"
    text += "2. Найдите и установите приложение «V2rayNG» или «ExpressVPN»\n"
    text += "3. Если Play Store недоступен, можно установить APK файл через USB-накопитель\n\n"
    
    text += "<b>Шаг 2:</b> Настройка соединения\n"
    text += "1. Откройте раздел «Мои подписки» в нашем боте на смартфоне\n"
    text += "2. Выберите активную подписку и нажмите «Получить конфигурацию»\n"
    text += "3. Выберите «Android» и скопируйте код\n"
    text += "4. Перенесите код на телевизор через облачное хранилище или QR-код\n"
    text += "5. В приложении VPN импортируйте конфигурацию\n\n"
    
    text += "<b>Метод 2: Для Samsung Smart TV, LG TV и других</b>\n\n"
    
    text += "Для телевизоров без возможности установки VPN-приложений рекомендуется настроить VPN на уровне маршрутизатора:\n"
    text += "1. Настройте VPN на вашем роутере по инструкции в разделе «Роутеры»\n"
    text += "2. Подключите Smart TV к этому роутеру\n"
    text += "3. Весь трафик телевизора будет идти через VPN\n\n"
    
    text += "<b>Метод 3: Использование устройств-посредников</b>\n\n"
    
    text += "Вы можете использовать дополнительные устройства для подключения VPN:\n"
    text += "• Amazon Fire TV Stick с установленным VPN-приложением\n"
    text += "• Apple TV с настроенным VPN-соединением\n"
    text += "• Google Chromecast с VPN на уровне роутера\n\n"
    
    text += "<b>Проверка соединения:</b>\n"
    text += "• Откройте браузер на Smart TV (если есть)\n"
    text += "• Перейдите на сайт 2ip.ru для проверки вашего IP-адреса\n"
    text += "• Или проверьте доступ к ранее заблокированным сервисам/приложениям\n\n"
    
    text += "⚠️ <b>Внимание:</b> Если у вас возникли трудности с настройкой VPN на вашем Smart TV, пожалуйста, обратитесь в нашу службу поддержки для получения персонализированной помощи."
    
    await callback.message.edit_text(
        text,
        reply_markup=get_instructions_back_keyboard('smarttv'),
        disable_web_page_preview=True
    )
    await callback.answer() 