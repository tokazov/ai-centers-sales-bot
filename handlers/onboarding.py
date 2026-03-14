"""Bot creation onboarding: channel select, voice/CRM setup, data collection, create bot."""

import logging
from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import urllib.request as _urllib
import json as _json
from core import bot, ADMIN_ID, get_session, detect_lang, t, get_plan_total_steps
from handlers.payments import get_plan_features
import os as _os
PHONE_SECRETARY_URL = _os.environ.get('PHONE_SECRETARY_URL', 'https://ai-phone-secretary-production.up.railway.app')

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(F.data.startswith("ob_channel_"))
async def on_ob_channel(callback: types.CallbackQuery):
    uid = callback.from_user.id
    session = get_session(uid)
    channel = callback.data.replace("ob_channel_", "")
    session["ob_channel"] = channel
    lang = session.get("lang", "ru")

    channel_names = {"telegram": "Telegram", "whatsapp": "WhatsApp", "website": "Сайт", "all": "Все каналы"}
    ch_name = channel_names.get(channel, channel)

    niche = session.get("ob_niche_name", "бизнес")
    biz_name = session.get("ob_biz_name", "Мой бизнес")
    tasks = session.get("ob_tasks", "общение с клиентами")

    # Remove Step 4 buttons
    try:
        await callback.message.edit_text(f"✅ Канал: <b>{ch_name}</b>")
    except Exception: pass
    await callback.answer()

    plan_key = session.get("plan", "starter")
    features = get_plan_features(plan_key)
    total = get_plan_total_steps(plan_key)

    # ── If Voice is available → Step 5: Voice Secretary setup ──
    if features.get("voice"):
        session["onboarding_step"] = 5
        voice_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📞 Использовать мой номер", callback_data="ob_voice_own")],
            [InlineKeyboardButton(text="🆕 Получить новый номер", callback_data="ob_voice_new")],
            [InlineKeyboardButton(text="⏭ Настроить позже", callback_data="ob_voice_skip")],
        ])
        await callback.message.answer(
            f"📋 <b>Шаг 5 из {total} — Голосовой AI-секретарь</b> 🗣\n\n"
            f"Ваш план <b>{features['label']}</b> включает AI-секретаря!\n\n"
            f"📞 AI отвечает на звонки голосом:\n"
            f"• Приветствует клиентов по имени\n"
            f"• Отвечает на вопросы о ценах и услугах\n"
            f"• Записывает на приём / принимает заказы\n"
            f"• Переводит на менеджера при необходимости\n\n"
            f"Как подключить?",
            reply_markup=voice_kb,
        )
        return

    # ── If CRM is available (but no Voice) → Step 5: CRM ──
    if features.get("crm"):
        session["onboarding_step"] = 6
        crm_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="AmoCRM", callback_data="ob_crm_amocrm"),
             InlineKeyboardButton(text="Bitrix24", callback_data="ob_crm_bitrix")],
            [InlineKeyboardButton(text="HubSpot", callback_data="ob_crm_hubspot"),
             InlineKeyboardButton(text="Google Sheets", callback_data="ob_crm_gsheets")],
            [InlineKeyboardButton(text="🚫 Пока без CRM", callback_data="ob_crm_skip")],
        ])
        step_num = 5 if not features.get("voice") else 6
        await callback.message.answer(
            f"📋 <b>Шаг {step_num} из {total} — CRM интеграция</b> 📊\n\n"
            f"Ваш план <b>{features['label']}</b> включает CRM!\n\n"
            f"AI-ассистент будет автоматически:\n"
            f"• Заносить новых клиентов в CRM\n"
            f"• Обновлять статусы сделок\n"
            f"• Отправлять уведомления менеджерам\n\n"
            f"Какую CRM-систему вы используете?",
            reply_markup=crm_kb,
        )
        return

    # ── Starter/Pro: no Voice, no CRM → straight to data collection ──
    session["onboarding"] = False
    session["onboarding_step"] = 0
    session["awaiting_data"] = True

    from handlers.messages import _show_data_collection
    await _show_data_collection(callback.message, session)

    # Notify admin
    user = callback.from_user
    if uid != ADMIN_ID:
        try:
            await bot.send_message(ADMIN_ID,
                f"🚀 <b>НОВЫЙ КЛИЕНТ!</b>\n\n"
                f"👤 {user.full_name}{(' (@' + user.username + ')') if user.username else ''}\n"
                f"🆔 {user.id}\n"
                f"🏢 {biz_name} ({niche})\n"
                f"📝 {tasks[:300]}\n"
                f"📱 {ch_name}")
        except Exception: pass


# ── Voice Secretary callbacks ──

@router.callback_query(F.data == "ob_voice_own")
async def on_ob_voice_own(callback: types.CallbackQuery):
    """Client wants to use their own phone number for voice AI."""
    session = get_session(callback.from_user.id)
    session["onboarding_step"] = 5
    session["ob_voice_type"] = "own"
    await callback.message.edit_text(
        "📞 <b>Ваш номер для AI-секретаря</b>\n\n"
        "Введите номер телефона в международном формате:\n"
        "<code>+995 XXX XXX XXX</code>\n\n"
        "На этот номер мы настроим переадресацию.\n"
        "Когда клиент звонит и вы не отвечаете — AI-секретарь подхватит! 👇"
    )
    await callback.answer()


@router.callback_query(F.data == "ob_voice_new")
async def on_ob_voice_new(callback: types.CallbackQuery):
    """Client wants a new number for voice AI."""
    session = get_session(callback.from_user.id)
    session["ob_voice_type"] = "new"
    session["ob_voice_phone"] = "new_number_requested"
    
    features = get_plan_features(session.get("plan", "starter"))
    total = get_plan_total_steps(session.get("plan", "starter"))

    await callback.message.edit_text(
        "🆕 <b>Новый номер для AI-секретаря</b>\n\n"
        "✅ Мы выделим вам номер с AI-секретарём.\n"
        "Номер будет готов в течение 24 часов.\n\n"
        "Вы получите уведомление когда всё настроено!"
    )
    await callback.answer()

    # Move to CRM or data collection
    if features.get("crm"):
        session["onboarding_step"] = 6
        crm_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="AmoCRM", callback_data="ob_crm_amocrm"),
             InlineKeyboardButton(text="Bitrix24", callback_data="ob_crm_bitrix")],
            [InlineKeyboardButton(text="HubSpot", callback_data="ob_crm_hubspot"),
             InlineKeyboardButton(text="Google Sheets", callback_data="ob_crm_gsheets")],
            [InlineKeyboardButton(text="🚫 Пока без CRM", callback_data="ob_crm_skip")],
        ])
        await callback.message.answer(
            f"📋 <b>Шаг 6 из {total} — CRM интеграция</b> 📊\n\n"
            f"AI-ассистент будет автоматически:\n"
            f"• Заносить новых клиентов в CRM\n"
            f"• Обновлять статусы сделок\n"
            f"• Отправлять уведомления менеджерам\n\n"
            f"Какую CRM-систему вы используете?",
            reply_markup=crm_kb,
        )
    else:
        session["onboarding"] = False
        session["onboarding_step"] = 0
        session["awaiting_data"] = True
        from handlers.messages import _show_data_collection
        await _show_data_collection(callback.message, session)


@router.callback_query(F.data == "ob_voice_skip")
async def on_ob_voice_skip(callback: types.CallbackQuery):
    """Client skips voice setup for now."""
    session = get_session(callback.from_user.id)
    session["ob_voice_phone"] = None

    features = get_plan_features(session.get("plan", "starter"))
    total = get_plan_total_steps(session.get("plan", "starter"))

    await callback.message.edit_text("⏭ Голосовой секретарь — настроите позже в управлении ботом.")
    await callback.answer()

    if features.get("crm"):
        session["onboarding_step"] = 6
        crm_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="AmoCRM", callback_data="ob_crm_amocrm"),
             InlineKeyboardButton(text="Bitrix24", callback_data="ob_crm_bitrix")],
            [InlineKeyboardButton(text="HubSpot", callback_data="ob_crm_hubspot"),
             InlineKeyboardButton(text="Google Sheets", callback_data="ob_crm_gsheets")],
            [InlineKeyboardButton(text="🚫 Пока без CRM", callback_data="ob_crm_skip")],
        ])
        await callback.message.answer(
            f"📋 <b>Шаг 6 из {total} — CRM интеграция</b> 📊\n\n"
            f"AI-ассистент будет автоматически:\n"
            f"• Заносить новых клиентов в CRM\n"
            f"• Обновлять статусы сделок\n"
            f"• Отправлять уведомления менеджерам\n\n"
            f"Какую CRM-систему вы используете?",
            reply_markup=crm_kb,
        )
    else:
        session["onboarding"] = False
        session["onboarding_step"] = 0
        session["awaiting_data"] = True
        from handlers.messages import _show_data_collection
        await _show_data_collection(callback.message, session)


# ── CRM callbacks ──

@router.callback_query(F.data.startswith("ob_crm_"))
async def on_ob_crm(callback: types.CallbackQuery):
    """Handle CRM selection during onboarding."""
    uid = callback.from_user.id
    session = get_session(uid)
    crm = callback.data.replace("ob_crm_", "")

    crm_names = {
        "amocrm": "AmoCRM", "bitrix": "Bitrix24",
        "hubspot": "HubSpot", "gsheets": "Google Sheets", "skip": None,
    }
    crm_name = crm_names.get(crm)

    if crm == "skip":
        session["ob_crm"] = None
        await callback.message.edit_text("⏭ CRM — настроите позже в управлении ботом.")
    else:
        session["ob_crm"] = crm
        await callback.message.edit_text(
            f"✅ CRM: <b>{crm_name}</b>\n\n"
            f"После создания бота мы пришлём инструкцию по подключению {crm_name}.\n"
            f"Интеграция занимает 5 минут!"
        )

    await callback.answer()

    # Move to data collection
    session["onboarding"] = False
    session["onboarding_step"] = 0
    session["awaiting_data"] = True

    from handlers.messages import _show_data_collection
    await _show_data_collection(callback.message, session)

    # Notify admin
    user = callback.from_user
    niche = session.get("ob_niche_name", "бизнес")
    biz_name = session.get("ob_biz_name", "Мой бизнес")
    tasks = session.get("ob_tasks", "")
    ch = session.get("ob_channel", "telegram")
    voice = session.get("ob_voice_phone", "—")
    channel_names = {"telegram": "Telegram", "whatsapp": "WhatsApp", "website": "Сайт", "all": "Все каналы"}

    if uid != ADMIN_ID:
        try:
            await bot.send_message(ADMIN_ID,
                f"🚀 <b>НОВЫЙ КЛИЕНТ!</b>\n\n"
                f"👤 {user.full_name}{(' (@' + user.username + ')') if user.username else ''}\n"
                f"🆔 {user.id}\n"
                f"🏢 {biz_name} ({niche})\n"
                f"📝 {tasks[:300]}\n"
                f"📱 {channel_names.get(ch, ch)}\n"
                f"🗣 Голос: {voice or '—'}\n"
                f"📊 CRM: {crm_name or '—'}\n"
                f"💼 План: {session.get('plan', '?')}")
        except Exception: pass


@router.callback_query(F.data == "ob_more_data")
async def on_ob_more_data(callback: types.CallbackQuery):
    session = get_session(callback.from_user.id)
    session["awaiting_data"] = True
    await callback.message.answer(
        "📎 Отправляйте ещё материалы:\n"
        "• Ссылки, фото, PDF, текст\n"
        "• Всё пойдёт на обучение бота 👇"
    )
    await callback.answer()


@router.callback_query(F.data == "ob_create_bot")
async def on_ob_create_bot(callback: types.CallbackQuery):
    uid = callback.from_user.id
    session = get_session(uid)
    session["awaiting_data"] = False

    biz_name = session.get("ob_biz_name", "Мой бизнес")
    niche = session.get("ob_niche_name", "бизнес")
    tasks = session.get("ob_tasks", "")
    ch = session.get("ob_channel", "telegram")
    data_count = len(session.get("ob_training_data", []))
    channel_names = {"telegram": "Telegram", "whatsapp": "WhatsApp", "website": "Сайт", "all": "Все каналы"}

    # Step 0: Offer demo call first
    await callback.message.edit_text(
        f"🚀 <b>Отлично! Почти готово.</b>\n\n"
        f"📊 <b>Ваши данные:</b>\n"
        f"• 🏢 {biz_name} ({niche})\n"
        f"• 📝 {tasks[:100]}\n"
        f"• 📱 {channel_names.get(ch, ch)}\n\n"
        f"{'─' * 25}\n\n"
        f"🎯 <b>Хотите услышать как будет звучать ваш ассистент?</b>\n\n"
        f"Позвоните — Алиса ответит от имени компании <b>{biz_name}</b>.\n"
        f"Это займёт 2 минуты.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📞 Сделать тестовый звонок", callback_data="ob_demo_call")],
            [InlineKeyboardButton(text="⏭ Пропустить, создать ассистента", callback_data="ob_skip_demo")],
        ]),
    )
    await callback.answer()
    return


@router.callback_query(F.data == "ob_skip_demo")
async def on_ob_skip_demo(callback: types.CallbackQuery):
    """Skip demo call, go straight to bot creation."""
    uid = callback.from_user.id
    session = get_session(uid)
    biz_name = session.get("ob_biz_name", "Мой бизнес")
    niche = session.get("ob_niche_name", "бизнес")
    tasks = session.get("ob_tasks", "")
    ch = session.get("ob_channel", "telegram")
    channel_names = {"telegram": "Telegram", "whatsapp": "WhatsApp", "website": "Сайт", "all": "Все каналы"}

    # Step 1: Ask to create bot in BotFather
    await callback.message.edit_text(
        f"🚀 <b>Отлично! Создаём бота.</b>\n\n"
        f"📊 <b>Параметры:</b>\n"
        f"• 🏢 {biz_name} ({niche})\n"
        f"• 📝 {tasks[:100]}\n"
        f"• 📱 {channel_names.get(ch, ch)}\n"
        f"• 📎 Материалов: {data_count}\n\n"
        f"{'─' * 25}\n\n"
        f"📱 <b>Теперь создайте бота в Telegram:</b>\n\n"
        f"1️⃣ Откройте @BotFather\n"
        f"2️⃣ Отправьте /newbot\n"
        f"3️⃣ Введите имя бота (например: <i>{biz_name}</i>)\n"
        f"4️⃣ Введите username (например: <i>{biz_name.lower().replace(' ', '_')}_bot</i>)\n"
        f"5️⃣ <b>Скопируйте токен</b> и отправьте его сюда 👇\n\n"
        f"Токен выглядит так:\n<code>1234567890:AAHxxxxx...</code>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🤖 Открыть @BotFather", url="https://t.me/BotFather")],
            [InlineKeyboardButton(text="❓ Не получается", callback_data="ob_help_botfather")],
        ]),
    )
    await callback.answer()

    session["awaiting_bot_token"] = True

    # Notify admin
    user = callback.from_user
    training = session.get("ob_training_data", [])
    data_summary = "\n".join([f"  {d['type']}: {d['text'][:200]}" for d in training[:5]])
    try:
        await bot.send_message(ADMIN_ID,
            f"🤖 <b>КЛИЕНТ СОЗДАЁТ БОТА!</b>\n\n"
            f"👤 {user.full_name}{(' (@' + user.username + ')') if user.username else ''}\n"
            f"🏢 {biz_name} ({niche})\n"
            f"📝 {tasks[:300]}\n"
            f"📱 {channel_names.get(ch, ch)}\n"
            f"📎 Данные ({data_count}):\n{data_summary}")
    except Exception: pass



# ── Demo call flow ──

@router.callback_query(F.data == "ob_demo_call")
async def on_ob_demo_call(callback: types.CallbackQuery):
    """Register caller phone for personalized demo and send call number."""
    uid = callback.from_user.id
    session = get_session(uid)
    
    biz_name = session.get("ob_biz_name", "Мой бизнес")
    niche = session.get("ob_niche", "other")
    
    await callback.message.edit_text(
        "📞 <b>Тестовый звонок</b>\n\n"
        "Введите ваш номер телефона в международном формате:\n"
        "<code>+7 900 000 00 00</code>\n"
        "<code>+995 555 000 000</code>\n\n"
        "Мы настроим ассистента под вашу компанию — и вы услышите его голос 👇"
    )
    await callback.answer()
    session["awaiting_demo_phone"] = True


@router.message(F.text)
async def on_demo_phone_input(message: types.Message):
    """Handle phone number input for demo call."""
    uid = message.from_user.id
    session = get_session(uid)
    
    if not session.get("awaiting_demo_phone"):
        return
    
    phone = message.text.strip()
    # Basic validation
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) < 9:
        await message.answer("❌ Неверный формат. Введите номер с кодом страны, например: +7 900 000 00 00")
        return
    
    if not phone.startswith("+"):
        phone = "+" + digits
    
    session["awaiting_demo_phone"] = False
    
    biz_name = session.get("ob_biz_name", "Мой бизнес")
    niche = session.get("ob_niche", "other")
    
    # Register demo tenant in phone secretary
    try:
        payload = _json.dumps({
            "company_name": biz_name,
            "niche": niche,
            "caller_phone": phone,
            "telegram_chat_id": str(uid)
        }).encode()
        req = _urllib.Request(
            f"{PHONE_SECRETARY_URL}/api/demo",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with _urllib.urlopen(req, timeout=10) as r:
            result = _json.loads(r.read())
        
        if result.get("ok"):
            await message.answer(
                f"✅ <b>Готово! Ассистент настроен на компанию «{biz_name}»</b>\n\n"
                f"📞 Позвоните прямо сейчас:\n"
                f"<b>+1 (447) 666-2643</b>\n\n"
                f"Алиса уже знает о вашей компании и ответит как ваш ассистент.\n"
                f"Ссылка действует 24 часа.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="✅ Подключить ассистента", callback_data="funnel_pricing")],
                    [InlineKeyboardButton(text="🔄 Позвонить ещё раз", callback_data="ob_demo_call")],
                ])
            )
        else:
            raise Exception(result.get("error", "unknown"))
    
    except Exception as e:
        logger.error(f"Demo call setup failed: {e}")
        # Fallback — give number anyway
        await message.answer(
            f"📞 <b>Позвоните для тестового звонка:</b>\n"
            f"<b>+1 (447) 666-2643</b>\n\n"
            f"Алиса ответит и расскажет о возможностях AI-ассистента.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Подключить ассистента", callback_data="funnel_pricing")],
            ])
        )
