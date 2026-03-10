"""Channel connection guides: Telegram, WhatsApp, Instagram, Website."""

import logging
from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core import bot, ADMIN_ID, get_session, detect_lang, t

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "guide_telegram")
async def on_guide_telegram(callback: types.CallbackQuery):
    session = get_session(callback.from_user.id)
    bot_username = session.get("created_bot_username", "ваш_бот")
    await callback.message.answer(
        f"📱 <b>Подключение к Telegram</b>\n\n"
        f"Выберите способ подключения @{bot_username}:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🤖 Отдельный бот (самый простой)", callback_data="tg_standalone")],
            [InlineKeyboardButton(text="💼 Бизнес-аккаунт (как сотрудник)", callback_data="tg_business")],
            [InlineKeyboardButton(text="👥 Группа / канал", callback_data="tg_group")],
            [InlineKeyboardButton(text="◀️ Другие каналы", callback_data="guide_back")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "tg_standalone")
async def on_tg_standalone(callback: types.CallbackQuery):
    session = get_session(callback.from_user.id)
    bot_username = session.get("created_bot_username", "ваш_бот")
    await callback.message.answer(
        f"🤖 <b>Отдельный бот</b>\n\n"
        f"Самый простой способ — бот уже работает!\n\n"
        f"<b>Ваша ссылка:</b>\n"
        f"<code>https://t.me/{bot_username}</code>\n\n"
        f"<b>Где разместить:</b>\n"
        f"• 🌐 На сайте — кнопка «Написать в Telegram»\n"
        f"• 📸 В Instagram bio\n"
        f"• 💬 В WhatsApp статусе\n"
        f"• 📧 В email подписи\n"
        f"• 🖨 На визитках, флаерах, меню\n"
        f"• 📋 В Google Maps / 2GIS\n\n"
        f"Клиент нажимает ссылку → попадает в чат с ботом → AI отвечает мгновенно ✅",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"🤖 Открыть @{bot_username}", url=f"https://t.me/{bot_username}")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="guide_telegram")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "tg_business")
async def on_tg_business(callback: types.CallbackQuery):
    session = get_session(callback.from_user.id)
    bot_username = session.get("created_bot_username", "ваш_бот")
    await callback.message.answer(
        f"💼 <b>Telegram Business аккаунт</b>\n\n"
        f"Бот отвечает <b>от имени вашего личного аккаунта</b>.\n"
        f"Клиент думает что общается с вами!\n\n"
        f"<b>Как подключить:</b>\n\n"
        f"1️⃣ Откройте <b>Настройки Telegram</b>\n"
        f"2️⃣ <b>Telegram Business</b> → <b>Чат-боты</b>\n"
        f"3️⃣ Выберите @{bot_username}\n"
        f"4️⃣ Настройте кто получает автоответ:\n"
        f"   • Все чаты\n"
        f"   • Только новые контакты\n"
        f"   • Выбранные чаты\n"
        f"5️⃣ Готово! Бот отвечает от вашего имени 🎉\n\n"
        f"⚠️ <b>Требуется Telegram Premium</b>\n\n"
        f"💡 Вы видите все диалоги и можете подключиться в любой момент",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="guide_telegram")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "tg_group")
async def on_tg_group(callback: types.CallbackQuery):
    session = get_session(callback.from_user.id)
    bot_username = session.get("created_bot_username", "ваш_бот")
    await callback.message.answer(
        f"👥 <b>Бот в группе / канале</b>\n\n"
        f"Бот отвечает на вопросы клиентов прямо в вашей группе.\n\n"
        f"<b>Как подключить:</b>\n\n"
        f"1️⃣ Откройте вашу группу в Telegram\n"
        f"2️⃣ Нажмите на название группы → <b>Участники</b>\n"
        f"3️⃣ <b>Добавить участника</b> → найдите @{bot_username}\n"
        f"4️⃣ Сделайте бота <b>администратором</b>\n"
        f"   (нужны права: читать и писать сообщения)\n"
        f"5️⃣ Готово! Бот отвечает в группе 🎉\n\n"
        f"💡 <b>Совет:</b> Создайте отдельную группу для клиентов.\n"
        f"Бот будет отвечать на частые вопросы, а вы — подключаться по необходимости.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="guide_telegram")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "guide_whatsapp")
async def on_guide_whatsapp(callback: types.CallbackQuery):
    session = get_session(callback.from_user.id)
    await callback.message.answer(
        f"💬 <b>Подключение к WhatsApp</b>\n\n"
        f"AI-бот будет отвечать клиентам в WhatsApp — автоматически, 24/7.\n"
        f"Выберите подходящий вариант:\n\n"
        f"{'─' * 25}\n\n"
        f"1️⃣ <b>У меня есть Meta Business</b> (бесплатно)\n"
        f"Если у вас уже настроен WhatsApp Business API через Meta — просто дайте нам токен доступа. Подключим за 5 минут.\n\n"
        f"2️⃣ <b>Подключить через Wazzup24</b> (~$30/мес)\n"
        f"Самый простой способ. Регистрация за 2 минуты, не нужна верификация Meta. WhatsApp + Instagram в одном сервисе.\n\n"
        f"3️⃣ <b>Подключить через Twilio</b> (оплата за сообщение)\n"
        f"Надёжная платформа. $0.005 за сообщение. Подходит для малого объёма или если уже пользуетесь Twilio.\n\n"
        f"4️⃣ <b>У меня только WhatsApp Business</b> (приложение)\n"
        f"Поможем настроить Meta Business и подключить API. Занимает 1-3 дня на верификацию.\n\n"
        f"{'─' * 25}\n\n"
        f"💡 <b>Результат одинаковый:</b>\n"
        f"Клиент пишет на ваш WhatsApp → AI отвечает мгновенно\n"
        f"Вы видите все диалоги и можете подключиться в любой момент",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💼 У меня есть Meta Business", callback_data="wa_meta")],
            [InlineKeyboardButton(text="⚡ Подключить через Wazzup24", callback_data="wa_wazzup")],
            [InlineKeyboardButton(text="📞 Подключить через Twilio", callback_data="wa_twilio")],
            [InlineKeyboardButton(text="📱 У меня только приложение", callback_data="wa_app_only")],
            [InlineKeyboardButton(text="◀️ Другие каналы", callback_data="guide_back")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "wa_meta")
async def on_wa_meta(callback: types.CallbackQuery):
    await callback.message.answer(
        "💼 <b>Подключение через Meta Business API</b>\n\n"
        "Бесплатно. 1000 сообщений/мес включены.\n\n"
        "Выберите шаг:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="1️⃣ Где найти API Setup", callback_data="meta_step1")],
            [InlineKeyboardButton(text="2️⃣ Получить токен", callback_data="meta_step2")],
            [InlineKeyboardButton(text="3️⃣ Отправить данные нам", callback_data="meta_step3")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="guide_whatsapp")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "meta_step1")
async def on_meta_step1(callback: types.CallbackQuery):
    await callback.message.answer(
        "1️⃣ <b>Где найти WhatsApp API Setup</b>\n\n"
        "1. Откройте <b>developers.facebook.com</b>\n"
        "2. Войдите в аккаунт Facebook\n"
        "3. Перейдите в <b>My Apps</b> (Мои приложения)\n"
        "4. Выберите ваше приложение (или создайте новое → тип «Business»)\n"
        "5. В левом меню: <b>WhatsApp</b> → <b>API Setup</b>\n\n"
        "Здесь вы увидите:\n"
        "• <b>Temporary Access Token</b> (временный — на 24 часа)\n"
        "• <b>Phone Number ID</b>\n"
        "• <b>WhatsApp Business Account ID</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🌐 Открыть Meta Developers", url="https://developers.facebook.com/apps/")],
            [InlineKeyboardButton(text="▶️ Дальше: получить токен", callback_data="meta_step2")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="wa_meta")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "meta_step2")
async def on_meta_step2(callback: types.CallbackQuery):
    await callback.message.answer(
        "2️⃣ <b>Получение постоянного токена</b>\n\n"
        "⚠️ Временный токен истекает через 24 часа. Нужен постоянный:\n\n"
        "1. В Meta Developers → ваше приложение\n"
        "2. <b>Business Settings</b> → <b>System Users</b>\n"
        "3. <b>Add System User</b> → имя: «AI Bot» → роль: <b>Admin</b>\n"
        "4. Нажмите <b>Generate New Token</b>\n"
        "5. Выберите приложение\n"
        "6. Включите разрешения:\n"
        "   ✅ <b>whatsapp_business_messaging</b>\n"
        "   ✅ <b>whatsapp_business_management</b>\n"
        "7. Нажмите <b>Generate Token</b>\n"
        "8. <b>Скопируйте токен!</b> Он показывается один раз!\n\n"
        "Также скопируйте <b>Phone Number ID</b> из WhatsApp → API Setup.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Дальше: отправить нам", callback_data="meta_step3")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="wa_meta")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "meta_step3")
async def on_meta_step3(callback: types.CallbackQuery):
    session = get_session(callback.from_user.id)
    session["awaiting_wa_token"] = True
    await callback.message.answer(
        "3️⃣ <b>Отправьте данные</b>\n\n"
        "Пришлите <b>два значения</b> в одном сообщении:\n\n"
        "<code>токен | phone_number_id</code>\n\n"
        "Например:\n"
        "<code>EAABsbCS1iHg... | 1234567890</code>\n\n"
        "Мы автоматически:\n"
        "✅ Подключим ваш WhatsApp к AI-боту\n"
        "✅ Настроим webhook\n"
        "✅ Отправим тестовое сообщение для проверки",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="meta_step2")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "wa_wazzup")
async def on_wa_wazzup(callback: types.CallbackQuery):
    await callback.message.answer(
        "⚡ <b>Подключение через Wazzup24</b>\n\n"
        "Wazzup24 подключает WhatsApp и Instagram к нашему AI без верификации Meta.\n\n"
        "💰 Стоимость: ~$30/мес\n"
        "🎁 WhatsApp + Instagram в одном сервисе\n\n"
        "Выберите шаг:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="1️⃣ Регистрация на Wazzup24", callback_data="wz_step1")],
            [InlineKeyboardButton(text="2️⃣ Подключение WhatsApp", callback_data="wz_step2")],
            [InlineKeyboardButton(text="3️⃣ Подключение Instagram", callback_data="wz_step3")],
            [InlineKeyboardButton(text="4️⃣ Получить API Key", callback_data="wz_step4")],
            [InlineKeyboardButton(text="5️⃣ Отправить API Key нам", callback_data="wz_step5")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="guide_whatsapp")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "wz_step1")
async def on_wz_step1(callback: types.CallbackQuery):
    await callback.message.answer(
        "1️⃣ <b>Регистрация на Wazzup24</b>\n\n"
        "1. Откройте <b>wazzup24.com</b>\n"
        "2. Нажмите <b>«Попробовать бесплатно»</b> или <b>«Регистрация»</b>\n"
        "3. Введите email и пароль\n"
        "4. Подтвердите email (придёт письмо)\n"
        "5. Войдите в личный кабинет ✅\n\n"
        "💡 Есть бесплатный пробный период — можно сначала протестировать!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🌐 Открыть Wazzup24", url="https://wazzup24.com")],
            [InlineKeyboardButton(text="▶️ Дальше: подключить WhatsApp", callback_data="wz_step2")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="wa_wazzup")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "wz_step2")
async def on_wz_step2(callback: types.CallbackQuery):
    await callback.message.answer(
        "2️⃣ <b>Подключение WhatsApp</b>\n\n"
        "1. В личном кабинете Wazzup24 нажмите <b>«Каналы»</b>\n"
        "2. Нажмите <b>«+ Добавить канал»</b>\n"
        "3. Выберите <b>«WhatsApp»</b>\n"
        "4. На экране появится <b>QR-код</b>\n"
        "5. Откройте WhatsApp на телефоне:\n"
        "   • <b>Android:</b> ⋮ меню → Связанные устройства → Привязать устройство\n"
        "   • <b>iPhone:</b> Настройки → Связанные устройства → Привязать устройство\n"
        "6. Наведите камеру на QR-код\n"
        "7. Подождите 10-30 секунд — статус станет <b>«Активен» ✅</b>\n\n"
        "⚠️ <b>Важно:</b> Телефон с WhatsApp должен быть подключён к интернету.\n"
        "Если связь потеряется — зайдите в Wazzup и пересканируйте QR.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Дальше: подключить Instagram", callback_data="wz_step3")],
            [InlineKeyboardButton(text="⏭ Пропустить Instagram", callback_data="wz_step4")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="wa_wazzup")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "wz_step3")
async def on_wz_step3(callback: types.CallbackQuery):
    await callback.message.answer(
        "3️⃣ <b>Подключение Instagram</b>\n\n"
        "1. В Wazzup24 → <b>«Каналы»</b> → <b>«+ Добавить канал»</b>\n"
        "2. Выберите <b>«Instagram»</b>\n"
        "3. Нажмите <b>«Войти через Facebook»</b>\n"
        "4. Авторизуйтесь в Facebook\n"
        "5. Выберите <b>Facebook Page</b>, привязанную к вашему Instagram\n"
        "6. Дайте все запрашиваемые разрешения\n"
        "7. Статус станет <b>«Активен» ✅</b>\n\n"
        "⚠️ <b>Для Instagram нужно:</b>\n"
        "• Бизнес-аккаунт Instagram (не личный)\n"
        "• Привязка к Facebook Page\n\n"
        "Если у вас личный аккаунт — переключите:\n"
        "Instagram → Настройки → Аккаунт → Переключить на бизнес",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Дальше: получить API Key", callback_data="wz_step4")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="wa_wazzup")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "wz_step4")
async def on_wz_step4(callback: types.CallbackQuery):
    await callback.message.answer(
        "4️⃣ <b>Получение API Key</b>\n\n"
        "1. В Wazzup24 откройте <b>«Настройки»</b> (⚙️ иконка)\n"
        "2. Перейдите в раздел <b>«API»</b> или <b>«Интеграции»</b>\n"
        "3. Нажмите <b>«Создать API Key»</b> (или он уже создан)\n"
        "4. Скопируйте ключ — это длинная строка букв и цифр\n\n"
        "Выглядит примерно так:\n"
        "<code>a1b2c3d4e5f6g7h8i9j0...</code>\n\n"
        "💡 <b>Не делитесь этим ключом ни с кем кроме нас!</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Дальше: отправить нам", callback_data="wz_step5")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="wa_wazzup")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "wz_step5")
async def on_wz_step5(callback: types.CallbackQuery):
    session = get_session(callback.from_user.id)
    session["awaiting_wazzup_key"] = True
    await callback.message.answer(
        "5️⃣ <b>Отправьте API Key</b>\n\n"
        "Вставьте скопированный API Key прямо сюда 👇\n\n"
        "Мы автоматически:\n"
        "✅ Подключим ваш WhatsApp к AI-боту\n"
        "✅ Подключим Instagram (если добавили)\n"
        "✅ Настроим webhook для получения сообщений\n"
        "✅ Протестируем и пришлём подтверждение\n\n"
        "Просто вставьте ключ:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="wz_step4")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "wa_app_only")
async def on_wa_app_only(callback: types.CallbackQuery):
    await callback.message.answer(
        "📱 <b>Настройка с нуля</b>\n\n"
        "У вас WhatsApp Business приложение — отлично, это первый шаг!\n\n"
        "<b>Есть 2 пути:</b>\n\n"
        "🅰️ <b>Быстрый (рекомендуем)</b>\n"
        "Зарегистрируйтесь на Wazzup24 → подключите номер через QR-код → готово за 5 минут.\n"
        "Стоимость ~$30/мес.\n\n"
        "🅱️ <b>Бесплатный (дольше)</b>\n"
        "Создайте Meta Business аккаунт → пройдите верификацию (3-7 дней) → подключите WhatsApp API.\n\n"
        "Что выбираете?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⚡ Быстрый (Wazzup24)", callback_data="wa_wazzup")],
            [InlineKeyboardButton(text="🆓 Бесплатный (Meta)", callback_data="wa_meta_setup")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="guide_whatsapp")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "wa_twilio")
async def on_wa_twilio(callback: types.CallbackQuery):
    await callback.message.answer(
        "📞 <b>Подключение через Twilio</b>\n\n"
        "Twilio — мировой лидер облачных коммуникаций.\n"
        "Оплата за сообщение (~$0.005). Бонус: SMS + звонки.\n\n"
        "Выберите шаг:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="1️⃣ Регистрация на Twilio", callback_data="tw_step1")],
            [InlineKeyboardButton(text="2️⃣ Активировать WhatsApp", callback_data="tw_step2")],
            [InlineKeyboardButton(text="3️⃣ Получить SID и Token", callback_data="tw_step3")],
            [InlineKeyboardButton(text="4️⃣ Отправить данные нам", callback_data="tw_step4")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="guide_whatsapp")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "tw_step1")
async def on_tw_step1(callback: types.CallbackQuery):
    await callback.message.answer(
        "1️⃣ <b>Регистрация на Twilio</b>\n\n"
        "1. Откройте <b>twilio.com</b>\n"
        "2. Нажмите <b>«Sign Up»</b> или <b>«Try for Free»</b>\n"
        "3. Введите email, имя, пароль\n"
        "4. Подтвердите email\n"
        "5. Подтвердите номер телефона (SMS код)\n"
        "6. На вопрос «What do you want to do?» выберите:\n"
        "   <b>Send WhatsApp messages</b>\n\n"
        "💡 Twilio даёт $15 бесплатного кредита для тестов!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🌐 Открыть Twilio", url="https://www.twilio.com/try-twilio")],
            [InlineKeyboardButton(text="▶️ Дальше: WhatsApp", callback_data="tw_step2")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="wa_twilio")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "tw_step2")
async def on_tw_step2(callback: types.CallbackQuery):
    await callback.message.answer(
        "2️⃣ <b>Активация WhatsApp в Twilio</b>\n\n"
        "<b>Для тестирования (бесплатно):</b>\n"
        "1. Console → Messaging → Try it Out → <b>Send a WhatsApp message</b>\n"
        "2. Twilio даст номер-sandbox\n"
        "3. Отправьте код на этот номер с вашего WhatsApp\n"
        "4. Sandbox активен ✅\n\n"
        "<b>Для продакшена:</b>\n"
        "1. Console → Messaging → Senders → <b>WhatsApp Senders</b>\n"
        "2. <b>Add WhatsApp Sender</b>\n"
        "3. Подключите ваш бизнес-номер\n"
        "4. Пройдите верификацию Meta (через Twilio — проще!)\n"
        "5. Номер активен ✅\n\n"
        "💡 Рекомендуем сначала протестировать на sandbox, потом перейти на продакшен.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Дальше: получить данные", callback_data="tw_step3")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="wa_twilio")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "tw_step3")
async def on_tw_step3(callback: types.CallbackQuery):
    await callback.message.answer(
        "3️⃣ <b>Получение Account SID и Auth Token</b>\n\n"
        "1. Откройте <b>Twilio Console</b> (console.twilio.com)\n"
        "2. На главной странице вы увидите блок <b>«Account Info»</b>\n"
        "3. Скопируйте:\n"
        "   • <b>Account SID</b> — начинается с AC...\n"
        "   • <b>Auth Token</b> — нажмите «Show» чтобы увидеть\n\n"
        "Выглядит так:\n"
        "<code>AC1234567890abcdef...</code>\n"
        "<code>abcdef1234567890...</code>\n\n"
        "💡 <b>Не делитесь этими данными ни с кем кроме нас!</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Дальше: отправить нам", callback_data="tw_step4")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="wa_twilio")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "tw_step4")
async def on_tw_step4(callback: types.CallbackQuery):
    session = get_session(callback.from_user.id)
    session["awaiting_twilio_token"] = True
    await callback.message.answer(
        "4️⃣ <b>Отправьте данные</b>\n\n"
        "Пришлите <b>два значения</b> в одном сообщении:\n\n"
        "<code>account_sid | auth_token</code>\n\n"
        "Например:\n"
        "<code>AC1a2b3c4d5e... | 9f8e7d6c5b4a...</code>\n\n"
        "Мы автоматически:\n"
        "✅ Подключим Twilio к вашему AI-боту\n"
        "✅ Настроим webhook для WhatsApp\n"
        "✅ Отправим тестовое сообщение для проверки",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="tw_step3")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "wa_meta_setup")
async def on_wa_meta_setup(callback: types.CallbackQuery):
    await callback.message.answer(
        "🆓 <b>Настройка Meta Business (бесплатно)</b>\n\n"
        "<b>Шаг 1:</b> Создайте аккаунт на business.facebook.com\n\n"
        "<b>Шаг 2:</b> Добавьте WhatsApp в Meta Business Suite\n"
        "Business Settings → Accounts → WhatsApp Accounts → Add\n\n"
        "<b>Шаг 3:</b> Пройдите верификацию бизнеса\n"
        "Загрузите документ (ИНН, выписка, счёт за коммуналку)\n"
        "Ожидание: 1-7 рабочих дней\n\n"
        "<b>Шаг 4:</b> Настройте WhatsApp API\n"
        "WhatsApp → API Setup → создайте Permanent Token\n\n"
        "<b>Шаг 5:</b> Отправьте токен и Phone Number ID сюда\n\n"
        "Если нужна помощь на любом шаге — просто напишите!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🌐 Открыть Meta Business", url="https://business.facebook.com")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="wa_app_only")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "guide_website")
async def on_guide_website(callback: types.CallbackQuery):
    session = get_session(callback.from_user.id)
    bot_username = session.get("created_bot_username", "ваш_бот")
    await callback.message.answer(
        f"🌐 <b>Подключение к сайту</b>\n\n"
        f"Чат-виджет в правом нижнем углу — клиенты пишут прямо на вашем сайте.\n"
        f"Выберите вашу платформу:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Универсальный код (любой сайт)", callback_data="web_code")],
            [InlineKeyboardButton(text="🔵 WordPress", callback_data="web_wordpress")],
            [InlineKeyboardButton(text="🟣 Tilda", callback_data="web_tilda")],
            [InlineKeyboardButton(text="🟠 Wix", callback_data="web_wix")],
            [InlineKeyboardButton(text="🟢 Shopify", callback_data="web_shopify")],
            [InlineKeyboardButton(text="🔗 Ссылка на чат (без сайта)", callback_data="web_link")],
            [InlineKeyboardButton(text="◀️ Другие каналы", callback_data="guide_back")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "web_code")
async def on_web_code(callback: types.CallbackQuery):
    session = get_session(callback.from_user.id)
    bot_username = session.get("created_bot_username", "ваш_бот")
    await callback.message.answer(
        f"📋 <b>Универсальный код виджета</b>\n\n"
        f"Работает на любом сайте. Вставьте один раз — виджет появится на всех страницах.\n\n"
        f"<b>Скопируйте этот код:</b>\n\n"
        f"<code>&lt;!-- AI Centers Chat Widget --&gt;\n"
        f"&lt;script\n"
        f"  src=\"https://ai-centers-dashboard-production.up.railway.app/widget/{bot_username}/embed\"\n"
        f"  async&gt;\n"
        f"&lt;/script&gt;</code>\n\n"
        f"<b>Куда вставить:</b>\n"
        f"Откройте HTML код вашего сайта и добавьте этот код перед <code>&lt;/body&gt;</code>\n\n"
        f"{'─' * 25}\n\n"
        f"🎨 <b>Настройка внешнего вида:</b>\n"
        f"Виджет автоматически использует цвета и название вашего бизнеса.\n"
        f"Хотите изменить цвета или логотип? Напишите нам!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="guide_website")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "web_wordpress")
async def on_web_wordpress(callback: types.CallbackQuery):
    session = get_session(callback.from_user.id)
    bot_username = session.get("created_bot_username", "ваш_бот")
    await callback.message.answer(
        f"🔵 <b>WordPress</b>\n\n"
        f"<b>Способ 1 — Через плагин (рекомендуем):</b>\n"
        f"1. Панель управления → Плагины → Добавить\n"
        f"2. Найдите <b>Insert Headers and Footers</b> → Установить\n"
        f"3. Настройки → Insert Headers and Footers\n"
        f"4. В поле <b>Footer</b> вставьте код виджета\n"
        f"5. Сохранить ✅\n\n"
        f"<b>Способ 2 — Через тему:</b>\n"
        f"1. Внешний вид → Редактор тем → footer.php\n"
        f"2. Перед <code>&lt;/body&gt;</code> вставьте код виджета\n"
        f"3. Сохранить ✅\n\n"
        f"<b>Способ 3 — Виджет HTML:</b>\n"
        f"1. Внешний вид → Виджеты\n"
        f"2. Добавить виджет «Произвольный HTML»\n"
        f"3. Вставьте код виджета\n\n"
        f"<b>Код:</b>\n"
        f"<code>&lt;script src=\"https://ai-centers-dashboard-production.up.railway.app/widget/{bot_username}/embed\" async&gt;&lt;/script&gt;</code>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="guide_website")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "web_tilda")
async def on_web_tilda(callback: types.CallbackQuery):
    session = get_session(callback.from_user.id)
    bot_username = session.get("created_bot_username", "ваш_бот")
    await callback.message.answer(
        f"🟣 <b>Tilda</b>\n\n"
        f"<b>Способ 1 — Блок HTML (на конкретную страницу):</b>\n"
        f"1. Откройте страницу в редакторе\n"
        f"2. Добавьте блок <b>T123 — HTML код</b>\n"
        f"3. Вставьте код виджета\n"
        f"4. Опубликуйте страницу ✅\n\n"
        f"<b>Способ 2 — На все страницы сайта:</b>\n"
        f"1. Настройки сайта → Ещё → HTML-код для вставки в &lt;/body&gt;\n"
        f"2. Вставьте код виджета\n"
        f"3. Опубликуйте все страницы ✅\n\n"
        f"<b>Код:</b>\n"
        f"<code>&lt;script src=\"https://ai-centers-dashboard-production.up.railway.app/widget/{bot_username}/embed\" async&gt;&lt;/script&gt;</code>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="guide_website")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "web_wix")
async def on_web_wix(callback: types.CallbackQuery):
    session = get_session(callback.from_user.id)
    bot_username = session.get("created_bot_username", "ваш_бот")
    await callback.message.answer(
        f"🟠 <b>Wix</b>\n\n"
        f"1. Откройте редактор сайта\n"
        f"2. Нажмите <b>+ Добавить</b> → <b>Embed Code</b> → <b>Custom Code</b>\n"
        f"3. Вставьте код виджета\n"
        f"4. Выберите расположение: <b>Body - end</b>\n"
        f"5. Применить на: <b>Все страницы</b>\n"
        f"6. Опубликуйте ✅\n\n"
        f"<b>Код:</b>\n"
        f"<code>&lt;script src=\"https://ai-centers-dashboard-production.up.railway.app/widget/{bot_username}/embed\" async&gt;&lt;/script&gt;</code>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="guide_website")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "web_shopify")
async def on_web_shopify(callback: types.CallbackQuery):
    session = get_session(callback.from_user.id)
    bot_username = session.get("created_bot_username", "ваш_бот")
    await callback.message.answer(
        f"🟢 <b>Shopify</b>\n\n"
        f"1. Админ-панель → <b>Online Store</b> → <b>Themes</b>\n"
        f"2. <b>Edit code</b> → найдите <b>theme.liquid</b>\n"
        f"3. Перед <code>&lt;/body&gt;</code> вставьте код виджета\n"
        f"4. Сохранить ✅\n\n"
        f"<b>Код:</b>\n"
        f"<code>&lt;script src=\"https://ai-centers-dashboard-production.up.railway.app/widget/{bot_username}/embed\" async&gt;&lt;/script&gt;</code>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="guide_website")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "web_link")
async def on_web_link(callback: types.CallbackQuery):
    session = get_session(callback.from_user.id)
    bot_username = session.get("created_bot_username", "ваш_бот")
    await callback.message.answer(
        f"🔗 <b>Ссылка на чат (без сайта)</b>\n\n"
        f"Нет своего сайта? Не проблема!\n\n"
        f"<b>Ваша ссылка на AI-чат:</b>\n"
        f"<code>https://ai-centers-dashboard-production.up.railway.app/widget/{bot_username}/embed</code>\n\n"
        f"<b>Где использовать:</b>\n"
        f"• 📸 В Instagram bio\n"
        f"• 💬 В WhatsApp статусе\n"
        f"• 📱 В TikTok профиле\n"
        f"• 📧 В email подписи\n"
        f"• 🖨 На визитках (QR-код)\n"
        f"• 📋 В Google Maps / 2GIS\n\n"
        f"А для Telegram — просто давайте клиентам ссылку:\n"
        f"<code>https://t.me/{bot_username}</code>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"🤖 Открыть @{bot_username}", url=f"https://t.me/{bot_username}")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="guide_website")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "guide_instagram")
async def on_guide_instagram(callback: types.CallbackQuery):
    session = get_session(callback.from_user.id)
    await callback.message.answer(
        f"📸 <b>Подключение к Instagram</b>\n\n"
        f"AI-бот отвечает на сообщения в Direct автоматически.\n"
        f"Выберите подходящий вариант:\n\n"
        f"{'─' * 25}\n\n"
        f"1️⃣ <b>У меня бизнес-аккаунт + Meta Business</b> (бесплатно)\n"
        f"Instagram привязан к Facebook Page → дайте нам токен страницы.\n"
        f"Подключим за 5 минут.\n\n"
        f"2️⃣ <b>Подключить через Wazzup24</b> (~$30/мес)\n"
        f"Самый простой путь. Сканируете QR-код — и Instagram подключён.\n"
        f"Бонус: WhatsApp в комплекте!\n\n"
        f"3️⃣ <b>У меня обычный/бизнес-аккаунт без Meta</b>\n"
        f"Поможем привязать Instagram к Facebook Page и настроить API.\n\n"
        f"{'─' * 25}\n\n"
        f"💡 <b>Результат:</b>\n"
        f"Клиент пишет в Direct → AI отвечает мгновенно\n"
        f"Отвечает на вопросы о ценах, бронях, наличии",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💼 У меня есть Meta Business", callback_data="ig_meta")],
            [InlineKeyboardButton(text="⚡ Подключить через Wazzup24", callback_data="wa_wazzup")],
            [InlineKeyboardButton(text="📱 Помогите настроить", callback_data="ig_setup")],
            [InlineKeyboardButton(text="◀️ Другие каналы", callback_data="guide_back")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "ig_meta")
async def on_ig_meta(callback: types.CallbackQuery):
    session = get_session(callback.from_user.id)
    session["awaiting_ig_token"] = True
    await callback.message.answer(
        "💼 <b>Подключение Instagram через Meta</b>\n\n"
        "<b>Нам нужны:</b>\n\n"
        "1️⃣ <b>Page Access Token</b>\n"
        "Meta Business Suite → Настройки → API → Generate Token\n"
        "(выберите страницу, привязанную к Instagram)\n\n"
        "2️⃣ <b>Instagram Business Account ID</b>\n"
        "Там же, в разделе Instagram Accounts\n\n"
        "Отправьте оба значения сюда 👇\n"
        "Формат: <code>токен | instagram_account_id</code>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="guide_instagram")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "ig_setup")
async def on_ig_setup(callback: types.CallbackQuery):
    await callback.message.answer(
        "📱 <b>Настройка Instagram для AI</b>\n\n"
        "<b>Шаг 1:</b> Переключите аккаунт на бизнес\n"
        "Instagram → Настройки → Аккаунт → Переключить на бизнес-аккаунт\n\n"
        "<b>Шаг 2:</b> Создайте Facebook Page (если нет)\n"
        "facebook.com → Создать → Страница → название бизнеса\n\n"
        "<b>Шаг 3:</b> Привяжите Instagram к Facebook Page\n"
        "Facebook Page → Настройки → Instagram → Подключить аккаунт\n\n"
        "<b>Шаг 4:</b> Выберите способ подключения API:\n\n"
        "🅰️ <b>Через Wazzup24</b> (быстро, ~$30/мес) — QR-код и готово\n"
        "🅱️ <b>Через Meta Business</b> (бесплатно, 3-7 дней верификация)\n\n"
        "Если нужна помощь — просто напишите что не получается!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⚡ Wazzup24 (быстро)", callback_data="wa_wazzup")],
            [InlineKeyboardButton(text="🆓 Meta Business (бесплатно)", callback_data="wa_meta_setup")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="guide_instagram")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "guide_back")
async def on_guide_back(callback: types.CallbackQuery):
    session = get_session(callback.from_user.id)
    bot_username = session.get("created_bot_username", "ваш_бот")
    connect_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Telegram", callback_data="guide_telegram")],
        [InlineKeyboardButton(text="💬 WhatsApp", callback_data="guide_whatsapp")],
        [InlineKeyboardButton(text="🌐 Сайт", callback_data="guide_website")],
        [InlineKeyboardButton(text="📸 Instagram", callback_data="guide_instagram")],
        [InlineKeyboardButton(text="📝 Доработать бота", callback_data="ob_customize_bot")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_menu")],
    ])
    await callback.message.answer(
        f"⚡ <b>Куда подключить @{bot_username}?</b>",
        reply_markup=connect_kb,
    )
    await callback.answer()


# ══════════════════════════════════════════
# BOT MANAGEMENT — post-creation help center
# ══════════════════════════════════════════

