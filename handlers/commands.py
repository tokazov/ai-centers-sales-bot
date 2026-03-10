"""Commands and menu callbacks: /start, /menu, /reset, /test_pay + menu items."""

import logging
from aiogram import Router, F, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from core import (
    SYSTEM_PROMPT, sessions, gemini_chat,
    bot, ADMIN_ID, get_session, detect_lang, t,
)
from handlers.payments import send_stars_invoice

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("reset"))
async def cmd_reset(message: types.Message):
    uid = message.from_user.id
    sessions[uid] = {"history": [], "count": 0, "mode": "receptionist", "persona": None}
    await message.answer("🔄 Начнём с чистого листа! Чем могу помочь?")


@router.message(Command("test_pay"))
async def cmd_test_pay(message: types.Message):
    """Admin-only: simulate payment → trigger onboarding."""
    if message.from_user.id != ADMIN_ID:
        return
    uid = message.from_user.id
    session = get_session(uid)
    lang = session.get("lang", "ru")

    await message.answer(
        "🎉 <b>Оплата прошла!</b> 250 ⭐ (тест)\n\n"
        "✅ План <b>Starter</b> активирован.\n"
        "Давайте настроим вашего AI-ассистента! 👇"
    )

    session["onboarding"] = True
    session["onboarding_step"] = 1

    ob_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍽 Ресторан / кафе", callback_data="ob_restaurant"),
         InlineKeyboardButton(text="🏥 Клиника", callback_data="ob_clinic")],
        [InlineKeyboardButton(text="💇 Салон красоты", callback_data="ob_salon"),
         InlineKeyboardButton(text="🛍 Магазин", callback_data="ob_shop")],
        [InlineKeyboardButton(text="💼 Услуги / B2B", callback_data="ob_services"),
         InlineKeyboardButton(text="📦 Другое", callback_data="ob_other")],
    ])

    await message.answer(
        "📋 <b>Шаг 1 из 4 — Ваш бизнес</b>\n\n"
        "Выберите нишу, чтобы AI-ассистент сразу знал специфику вашей работы:",
        reply_markup=ob_kb,
    )


@router.message(Command("menu"))
async def cmd_menu(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✨ Создать AI-помощника", callback_data="create")],
        [InlineKeyboardButton(text="⚙️ Управление ботом", callback_data="ob_manage_bot")],
        [InlineKeyboardButton(text="🖥 Computer Use (CRM, 1C, таблицы)", callback_data="computer_use")],
        [InlineKeyboardButton(text="🤖 Каталог агентов", web_app=WebAppInfo(url="https://aicenters.co/miniapp.html"))],
        [InlineKeyboardButton(text="🗣️ Голосовой AI-секретарь", callback_data="voice_ai")],
        [InlineKeyboardButton(text="⭐ Тарифы и оплата", callback_data="pricing")],
        [InlineKeyboardButton(text="🤝 Партнёрская программа", url="https://t.me/aicenters_hub_bot?start=partner")],
        [InlineKeyboardButton(text="🌐 Сайт", url="https://aicenters.co")],
    ])
    await message.answer("Вот что у нас есть:", reply_markup=kb)


@router.callback_query(F.data == "create")

async def on_create(callback: types.CallbackQuery):
    uid = callback.from_user.id
    session = get_session(uid)
    session["mode"] = "receptionist"
    
    lang = session.get("lang", detect_lang(callback.from_user))
    response = gemini_chat(SYSTEM_PROMPT, session["history"], "Я хочу создать своего AI-помощника")
    session["history"].append({"user": "Хочу создать AI-помощника", "bot": response})
    
    action_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_order_assistant"), callback_data="funnel_pricing")],
        [InlineKeyboardButton(text="🎯 Демо", callback_data="funnel_demo"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_menu")],
    ])
    await callback.message.answer(response, reply_markup=action_kb)
    await callback.answer()


@router.callback_query(F.data == "computer_use")
async def on_computer_use(callback: types.CallbackQuery):
    uid = callback.from_user.id
    session = get_session(uid)

    text = (
        "🖥 <b>AI Computer Use</b>\n\n"
        "AI-сотрудник, который сам работает в ваших программах:\n\n"
        "• <b>AmoCRM / Bitrix24</b> — заполняет карточки, двигает сделки, ставит задачи\n"
        "• <b>1C</b> — создаёт накладные, обновляет остатки\n"
        "• <b>Google Таблицы</b> — собирает данные, строит отчёты\n"
        "• <b>Маркетплейсы</b> — мониторит заказы, отвечает покупателям\n\n"
        "⚡ Работает без API — видит экран как человек\n"
        "⏱ Пилот за 3 дня | 24/7 | от $39/мес\n\n"
        "Настройка процесса: от $299 (разово)"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Подробнее на сайте", url="https://aicenters.co/computer-use")],
        [InlineKeyboardButton(text="🎯 Запланировать демо", callback_data="computer_use_demo")],
        [InlineKeyboardButton(text="💰 Тарифы Computer Use", url="https://aicenters.co/computer-use#pricing")],
        [InlineKeyboardButton(text="← Меню", callback_data="back_menu")],
    ])

    await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "computer_use_demo")
async def on_computer_use_demo(callback: types.CallbackQuery):
    uid = callback.from_user.id
    session = get_session(uid)

    response = gemini_chat(SYSTEM_PROMPT, session["history"],
        "[Система: клиент нажал 'Запланировать демо Computer Use'. "
        "Спроси: 1) В какой системе работает (AmoCRM, Bitrix, 1C, Google Sheets, другое)? "
        "2) Какой процесс хочет автоматизировать? "
        "3) Удобное время для демо (30 мин, онлайн). "
        "Будь коротким и конкретным.]")
    session["history"].append({"user": "Хочу демо Computer Use", "bot": response})

    await callback.message.answer(response)
    await callback.answer()


# ─── Computer Use Pilot Callbacks ───

@router.callback_query(F.data.startswith("cu_sys_"))
async def on_cu_system(callback: types.CallbackQuery):
    uid = callback.from_user.id
    session = get_session(uid)
    lang = session.get("lang", "ru")
    system_map = {"cu_sys_amocrm": "AmoCRM", "cu_sys_bitrix": "Bitrix24", "cu_sys_1c": "1C", "cu_sys_gsheets": "Google Sheets", "cu_sys_other": "Другое"}
    system = system_map.get(callback.data, callback.data)

    if not session.get("cu_pilot_data"):
        session["cu_pilot_data"] = {}
    session["cu_pilot_data"]["system"] = system
    session["cu_pilot_step"] = 2

    q2 = {
        "ru": "<b>2/3. Какой процесс хотите автоматизировать?</b>\n\nНапример: выставление счетов, перенос данных, рассылка...",
        "en": "<b>2/3. What process do you want to automate?</b>\n\nFor example: invoicing, data migration, mailing...",
    }
    await callback.message.answer(q2.get(lang, q2["en"]))
    await callback.answer()


# ─── Computer Use text handler (pilot steps 2-3 + demo) ───

@router.callback_query(F.data == "back_menu")
async def on_back_menu(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✨ Создать AI-помощника", callback_data="create")],
        [InlineKeyboardButton(text="⚙️ Управление ботом", callback_data="ob_manage_bot")],
        [InlineKeyboardButton(text="🖥 Computer Use (CRM, 1C, таблицы)", callback_data="computer_use")],
        [InlineKeyboardButton(text="🤖 Каталог агентов", web_app=WebAppInfo(url="https://aicenters.co/miniapp.html"))],
        [InlineKeyboardButton(text="🗣️ Голосовой AI-секретарь", callback_data="voice_ai")],
        [InlineKeyboardButton(text="⭐ Тарифы и оплата", callback_data="pricing")],
        [InlineKeyboardButton(text="🤝 Партнёрская программа", url="https://t.me/aicenters_hub_bot?start=partner")],
        [InlineKeyboardButton(text="🌐 Сайт", url="https://aicenters.co")],
    ])
    await callback.message.answer("Вот что у нас есть:", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "catalog")
async def on_catalog(callback: types.CallbackQuery):
    uid = callback.from_user.id
    session = get_session(uid)
    
    response = gemini_chat(SYSTEM_PROMPT, session["history"], "Покажи каталог готовых агентов. Какие есть?")
    session["history"].append({"user": "Покажи каталог", "bot": response})
    
    await callback.message.answer(response)
    await callback.answer()


@router.callback_query(F.data == "voice_ai")
async def on_voice_ai(callback: types.CallbackQuery):
    uid = callback.from_user.id
    session = get_session(uid)
    
    response = gemini_chat(SYSTEM_PROMPT, session["history"],
        "[Система: клиент нажал кнопку 'Голосовой AI-секретарь'. Расскажи коротко что это: AI отвечает клиентам реалистичным голосом 24/7, от $300/мес. Спроси какой у него бизнес.]")
    session["history"].append({"user": "Расскажи про голосового AI-секретаря", "bot": response})
    
    await callback.message.answer(response)
    await callback.answer()


@router.callback_query(F.data == "pricing")
async def on_pricing(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Неделя — 150 Stars (~$2.5)", callback_data="pay_week")],
        [InlineKeyboardButton(text="⭐ Месяц — 500 Stars (~$8)", callback_data="pay_month")],
        [InlineKeyboardButton(text="👑 Премиум — 1500 Stars (~$25)", callback_data="pay_premium")],
        [InlineKeyboardButton(text="🤖 Бот под ключ — от $499", url="https://t.me/timurtokazov")],
        [InlineKeyboardButton(text="🗣️ Голосовой секретарь — от $300/мес", url="https://t.me/timurtokazov")],
    ])
    await callback.message.answer(
        "⭐ <b>Тарифы AI Centers</b>\n\n"
        "🆓 <b>Бесплатно:</b> 20 сообщений с любым агентом\n\n"
        "⭐ <b>Подписка через Telegram Stars:</b>\n"
        "• Неделя — 150 ⭐ (~$2.5)\n"
        "• Месяц — 500 ⭐ (~$8)\n"
        "• Премиум — 1500 ⭐ (~$25)\n\n"
        "🤖 <b>Бот под ключ:</b> от $499\n"
        "🗣️ <b>Голосовой AI-секретарь:</b> от $300/мес\n\n"
        "Выбери тариф:", reply_markup=kb)
    await callback.answer()

