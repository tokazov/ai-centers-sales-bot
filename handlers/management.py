"""Bot management: train, edit, billing, FAQ, customize, stats, niche."""

import logging
from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core import bot, ADMIN_ID, get_session, detect_lang, t
from handlers.payments import paid_users

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(F.data == "ob_manage_bot")
async def on_manage_bot(callback: types.CallbackQuery):
    session = get_session(callback.from_user.id)
    bot_username = session.get("created_bot_username", "ваш бот")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧠 Обучить бота", callback_data="manage_train")],
        [InlineKeyboardButton(text="✏️ Изменить ответы и стиль", callback_data="manage_edit")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="ob_bot_stats")],
        [InlineKeyboardButton(text="💰 Тариф и оплата", callback_data="manage_billing")],
        [InlineKeyboardButton(text="🔌 Подключить каналы", callback_data="guide_back")],
        [InlineKeyboardButton(text="❓ FAQ", callback_data="manage_faq")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_menu")],
    ])
    await callback.message.answer(
        f"⚙️ <b>Управление ботом @{bot_username}</b>\n\n"
        f"Выберите что хотите сделать:",
        reply_markup=kb,
    )
    await callback.answer()


@router.callback_query(F.data == "manage_train")
async def on_manage_train(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📎 Отправить ссылку на сайт", callback_data="ob_send_url")],
        [InlineKeyboardButton(text="📄 Загрузить файл (PDF/фото)", callback_data="ob_send_price")],
        [InlineKeyboardButton(text="✏️ Написать текстом", callback_data="ob_send_desc")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="ob_manage_bot")],
    ])
    await callback.message.answer(
        "🧠 <b>Обучение бота</b>\n\n"
        "Бот учится на ваших данных. Чем больше информации — тем умнее ответы.\n\n"
        "<b>Что можно отправить:</b>\n\n"
        "📎 <b>Ссылка на сайт</b>\n"
        "Бот прочитает сайт и выучит всю информацию\n\n"
        "📄 <b>Файлы</b>\n"
        "Прайс-лист, меню, каталог (PDF, фото, документы)\n\n"
        "✏️ <b>Текст</b>\n"
        "Напишите FAQ, описание услуг, частые вопросы\n\n"
        "💬 <b>Примеры диалогов</b>\n"
        "Скопируйте реальные переписки с клиентами — бот научится отвечать так же\n\n"
        "📸 <b>Фото</b>\n"
        "Фото меню, витрины, прайса — бот распознает текст\n\n"
        "💡 Можно отправлять данные в любой момент — бот дообучается автоматически!",
        reply_markup=kb,
    )
    await callback.answer()


@router.callback_query(F.data == "manage_edit")
async def on_manage_edit(callback: types.CallbackQuery):
    session = get_session(callback.from_user.id)
    session["awaiting_data"] = "edit_request"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="ob_manage_bot")],
    ])
    await callback.message.answer(
        "✏️ <b>Изменить бота</b>\n\n"
        "Напишите что хотите изменить. Примеры:\n\n"
        "💬 <b>Стиль общения:</b>\n"
        "«Пусть бот обращается на вы и говорит формально»\n"
        "«Добавь эмодзи и неформальный тон»\n\n"
        "📝 <b>Ответы:</b>\n"
        "«На вопрос о доставке отвечай: доставка бесплатная от 50 лари»\n"
        "«Не говори клиентам про скидки без спроса»\n\n"
        "🔧 <b>Функции:</b>\n"
        "«Добавь кнопку «Позвонить нам»»\n"
        "«Спрашивай номер телефона при заказе»\n"
        "«Отправляй меню когда спрашивают про еду»\n\n"
        "Просто опишите — мы обновим бота 👇",
        reply_markup=kb,
    )
    await callback.answer()


@router.callback_query(F.data == "manage_billing")
async def on_manage_billing(callback: types.CallbackQuery):
    uid = callback.from_user.id
    session = get_session(uid)
    current_plan = paid_users.get(uid, {}).get("plan", "нет")
    plan_names = {"starter": "Starter ($19/мес)", "pro": "Pro ($49/мес)", "business": "Business ($79/мес)", "week": "Неделя", "month": "Месяц"}
    plan_display = plan_names.get(current_plan, current_plan)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬆️ Улучшить тариф", callback_data="funnel_pricing")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="ob_manage_bot")],
    ])
    await callback.message.answer(
        f"💰 <b>Тариф и оплата</b>\n\n"
        f"📦 Текущий план: <b>{plan_display}</b>\n\n"
        f"<b>Что входит в тарифы:</b>\n\n"
        f"⭐ <b>Starter</b> — $149 + $19/мес\n"
        f"• 1 AI-бот, Telegram + WhatsApp\n"
        f"• Обучение на ваших данных\n\n"
        f"🚀 <b>Pro</b> — $299 + $49/мес\n"
        f"• 3 AI-бота, CRM интеграция\n"
        f"• Приоритетная поддержка\n\n"
        f"🏢 <b>Business</b> — $499 + $79/мес\n"
        f"• 10 AI-ботов, API + webhook\n"
        f"• Персональный менеджер\n\n"
        f"💳 Оплата: Telegram Stars, криптовалюта, банковский перевод",
        reply_markup=kb,
    )
    await callback.answer()


@router.callback_query(F.data == "manage_faq")
async def on_manage_faq(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="ob_manage_bot")],
    ])
    await callback.message.answer(
        "❓ <b>Частые вопросы</b>\n\n"
        "<b>Бот не отвечает. Что делать?</b>\n"
        "→ Убедитесь что бот запущен (напишите ему /start). Если не помогло — напишите нам.\n\n"
        "<b>Можно изменить ответы бота?</b>\n"
        "→ Да! Отправьте новые данные или опишите что изменить — мы обновим.\n\n"
        "<b>Бот отвечает неправильно. Как исправить?</b>\n"
        "→ Скриншот неправильного ответа + как должно быть → отправьте нам.\n\n"
        "<b>Можно подключить несколько каналов?</b>\n"
        "→ Да! Telegram + WhatsApp + сайт + Instagram — всё одновременно.\n\n"
        "<b>Клиенты видят что это бот?</b>\n"
        "→ Зависит от подключения. Через Telegram Business — клиент думает что пишет вам лично.\n\n"
        "<b>Как отменить подписку?</b>\n"
        "→ Напишите нам «отмена» — отключим в тот же день.\n\n"
        "<b>Бот работает на каких языках?</b>\n"
        "→ На всех! AI автоматически определяет язык клиента и отвечает на нём.\n\n"
        "<b>Мои данные в безопасности?</b>\n"
        "→ Да. Данные хранятся зашифрованно. Доступ только у вас.",
        reply_markup=kb,
    )
    await callback.answer()


@router.callback_query(F.data == "ob_customize_bot")
async def on_ob_customize(callback: types.CallbackQuery):
    session = get_session(callback.from_user.id)
    bot_username = session.get("created_bot_username", "ваш бот")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📄 Обновить данные / прайс", callback_data="ob_send_desc")],
        [InlineKeyboardButton(text="📎 Добавить ссылку на сайт", callback_data="ob_send_url")],
        [InlineKeyboardButton(text="💬 Написать что изменить", callback_data="ob_send_custom_request")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_menu")],
    ])
    await callback.message.answer(
        f"🔧 <b>Доработка @{bot_username}</b>\n\n"
        f"Что хотите изменить?\n"
        f"• Обновить информацию (цены, меню, услуги)\n"
        f"• Изменить стиль общения\n"
        f"• Добавить новые возможности\n\n"
        f"Выберите или просто напишите что нужно 👇",
        reply_markup=kb,
    )
    await callback.answer()


@router.callback_query(F.data == "ob_send_custom_request")
async def on_ob_custom_request(callback: types.CallbackQuery):
    session = get_session(callback.from_user.id)
    session["awaiting_data"] = "custom_request"
    await callback.message.answer(
        "✏️ <b>Опишите что нужно изменить</b>\n\n"
        "Например:\n"
        "• «Добавь в меню новые блюда: ...»\n"
        "• «Пусть бот спрашивает номер телефона при заказе»\n"
        "• «Измени приветствие на ...»\n\n"
        "Просто напишите 👇"
    )
    await callback.answer()


@router.callback_query(F.data == "ob_bot_stats")
async def on_ob_bot_stats(callback: types.CallbackQuery):
    await callback.message.answer(
        "📊 <b>Статистика бота</b>\n\n"
        "Статистика будет доступна после первых диалогов с клиентами.\n\n"
        "Вы увидите:\n"
        "• 💬 Количество диалогов\n"
        "• ⭐ Конверсия в заказ/бронь\n"
        "• 📈 Популярные вопросы\n"
        "• ⏱ Среднее время ответа\n\n"
        "Начните привлекать клиентов — данные появятся автоматически!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_menu")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "ob_help_botfather")
async def on_ob_help_botfather(callback: types.CallbackQuery):
    await callback.message.answer(
        "🆘 <b>Инструкция по созданию бота:</b>\n\n"
        "1. Откройте Telegram и найдите @BotFather\n"
        "2. Нажмите Start или отправьте /newbot\n"
        "3. BotFather спросит имя — введите название вашего бизнеса\n"
        "4. BotFather спросит username — придумайте уникальное имя, заканчивающееся на _bot\n"
        "5. Вы получите длинный токен — скопируйте его\n"
        "6. Вставьте токен прямо сюда, в этот чат\n\n"
        "📹 Если не получается — напишите «помощь» и я помогу пошагово!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🤖 Открыть @BotFather", url="https://t.me/BotFather")],
        ]),
    )
    await callback.answer()


@router.callback_query(F.data == "ob_send_url")
async def on_ob_send_url(callback: types.CallbackQuery):
    session = get_session(callback.from_user.id)
    session["awaiting_data"] = "url"
    await callback.message.answer(
        "🌐 <b>Отправьте ссылку на ваш сайт</b>\n\n"
        "Мы изучим сайт и обучим бота на его содержимом — меню, цены, услуги, FAQ.\n\n"
        "Просто отправьте URL 👇"
    )
    await callback.answer()


@router.callback_query(F.data == "ob_send_menu")
async def on_ob_send_menu(callback: types.CallbackQuery):
    session = get_session(callback.from_user.id)
    session["awaiting_data"] = "menu"
    await callback.message.answer(
        "🍽 <b>Загрузите меню ресторана</b>\n\n"
        "Отправьте фото меню, PDF-файл или текстом:\n"
        "• Названия блюд и цены\n"
        "• Категории (салаты, горячее, напитки)\n"
        "• Калорийность (если есть) — бот сможет рассказать клиентам!\n\n"
        "📸 Фото / 📄 PDF / ✏️ Текст — что удобнее 👇"
    )
    await callback.answer()


@router.callback_query(F.data.in_({"ob_send_price", "ob_send_catalog"}))
async def on_ob_send_price(callback: types.CallbackQuery):
    session = get_session(callback.from_user.id)
    session["awaiting_data"] = "price"
    niche_key = session.get("ob_niche", "other")
    if niche_key == "shop":
        text = "🛍 <b>Загрузите каталог товаров</b>\n\nОтправьте фото, PDF или текстом:\n• Названия и цены\n• Категории\n• Наличие\n\n📸 Фото / 📄 PDF / ✏️ Текст 👇"
    else:
        text = "📄 <b>Загрузите прайс-лист</b>\n\nОтправьте фото, PDF или текстом:\n• Услуги и цены\n• Длительность\n• Акции / скидки\n\n📸 Фото / 📄 PDF / ✏️ Текст 👇"
    await callback.message.answer(text)
    await callback.answer()


@router.callback_query(F.data == "ob_send_desc")
async def on_ob_send_desc(callback: types.CallbackQuery):
    session = get_session(callback.from_user.id)
    session["awaiting_data"] = "desc"
    await callback.message.answer(
        "📝 <b>Опишите ваш бизнес</b>\n\n"
        "Расскажите в свободной форме:\n"
        "• Чем занимаетесь\n"
        "• Какие услуги / товары\n"
        "• Частые вопросы клиентов\n"
        "• Цены (если есть)\n\n"
        "Чем подробнее — тем умнее бот 👇"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ob_"))
async def on_ob_niche(callback: types.CallbackQuery):
    uid = callback.from_user.id
    session = get_session(uid)
    niche = callback.data.replace("ob_", "")
    session["ob_niche"] = niche
    session["onboarding_step"] = 2
    lang = session.get("lang", "ru")

    niche_names = {
        "restaurant": "Ресторан / кафе", "clinic": "Клиника", "salon": "Салон красоты",
        "shop": "Магазин", "services": "Услуги / B2B", "other": "Другое",
    }
    session["ob_niche_name"] = niche_names.get(niche, niche)

    await callback.message.edit_text(
        f"✅ Ниша: <b>{session['ob_niche_name']}</b>\n\n"
        f"📋 <b>Шаг 2 из 4 — Название бизнеса</b>\n\n"
        f"Напишите название вашей компании (как клиенты вас знают).\n"
        f"Например: <i>Ресторан «У Георгия»</i>",
    )
    await callback.answer()


# Step 2: Business name (text input)
# Step 3: What should bot do (text input)
# These are handled in the main message handler


