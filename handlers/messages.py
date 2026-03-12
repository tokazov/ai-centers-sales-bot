"""Message handlers: text input, voice, speech-to-text.

Contains the main on_text handler (routing by session state)
and on_voice handler.
"""

import os
import json
import logging
import urllib.request
import asyncio
import aiohttp
from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile

from handlers.payments import STAR_PLANS
from core import (
    SYSTEM_PROMPT, ASSISTANT_SYSTEM,
    bot, ADMIN_ID, PLATFORM_API_URL, PLATFORM_API_KEY,
    OPENAI_KEY, GEMINI_KEY, GEMINI_MODEL,
    ENGINE_API_URL, TOKEN,
    get_session, is_paid, detect_lang, t,
    check_rate_limit, detect_injection, gemini_chat, send_with_voice,
    FREE_LIMIT, VOICE_ENABLED,
    sessions,
)

logger = logging.getLogger(__name__)
router = Router()

async def _show_data_collection(message, session):
    """Show data collection prompt after all onboarding steps."""
    niche = session.get("ob_niche_name", "бизнес")
    biz_name = session.get("ob_biz_name", "Мой бизнес")
    tasks = session.get("ob_tasks", "общение с клиентами")

    # Build summary of what was configured
    extras = []
    if session.get("ob_voice_phone"):
        extras.append(f"• 🗣 Голос: {session['ob_voice_phone']}")
    if session.get("ob_crm"):
        crm_names = {"amocrm": "AmoCRM", "bitrix": "Bitrix24", "hubspot": "HubSpot", "gsheets": "Google Sheets"}
        extras.append(f"• 📊 CRM: {crm_names.get(session['ob_crm'], session['ob_crm'])}")

    extra_text = "\n".join(extras)
    if extra_text:
        extra_text = "\n" + extra_text + "\n"

    summary = (
        f"🎉 <b>Настройка завершена!</b>\n\n"
        f"📊 <b>Ваш AI-ассистент:</b>\n"
        f"• Бизнес: {biz_name} ({niche})\n"
        f"• Задачи: {tasks[:200]}\n"
        f"{extra_text}\n"
        f"⚡ <b>Теперь отправьте материалы для обучения:</b>\n"
        f"• 📎 Ссылка на сайт\n"
        f"• 📄 Прайс-лист, меню, FAQ\n"
        f"• 💬 Примеры переписок с клиентами\n\n"
        f"Чем больше данных — тем умнее бот. 👇"
    )

    niche_key = session.get("ob_niche", "other")
    buttons = [
        [InlineKeyboardButton(text="📎 Отправить ссылку на сайт", callback_data="ob_send_url")],
    ]
    if niche_key == "restaurant":
        buttons.append([InlineKeyboardButton(text="🍽 Загрузить меню ресторана", callback_data="ob_send_menu")])
    elif niche_key in ("clinic", "salon"):
        buttons.append([InlineKeyboardButton(text="📄 Загрузить прайс услуг", callback_data="ob_send_price")])
    elif niche_key == "shop":
        buttons.append([InlineKeyboardButton(text="🛍 Загрузить каталог товаров", callback_data="ob_send_catalog")])
    else:
        buttons.append([InlineKeyboardButton(text="📄 Загрузить прайс / каталог", callback_data="ob_send_price")])
    buttons.append([InlineKeyboardButton(text="💬 Написать описание бизнеса", callback_data="ob_send_desc")])
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_menu")])

    await message.answer(summary, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


# Cross-module imports (lazy to avoid circular)
def _get_handle_cu_text():
    from handlers.computer_use import handle_cu_text
    return handle_cu_text

def _get_show_funnel_step1():
    from handlers.funnel import show_funnel_step1
    return show_funnel_step1

from handlers.payments import STAR_PLANS
def _get_send_stars_invoice():
    from handlers.payments import send_stars_invoice
    return send_stars_invoice


async def speech_to_text(ogg_bytes: bytes) -> str:
    """Convert voice message to text using OpenAI Whisper."""
    if not OPENAI_KEY:
        return ""
    boundary = "----FormBoundary7MA4YWxkTrZu0gW"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="voice.ogg"\r\n'
        f"Content-Type: audio/ogg\r\n\r\n"
    ).encode() + ogg_bytes + (
        f"\r\n--{boundary}\r\n"
        f'Content-Disposition: form-data; name="model"\r\n\r\n'
        f"whisper-1\r\n"
        f"--{boundary}--\r\n"
    ).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/audio/transcriptions",
        data=body,
        headers={
            "Authorization": f"Bearer {OPENAI_KEY}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST"
    )
    loop = asyncio.get_event_loop()
    resp = await loop.run_in_executor(None, lambda: urllib.request.urlopen(req, timeout=30))
    result = json.loads(resp.read().decode())
    return result.get("text", "")


@router.message(F.voice)
async def on_voice(message: types.Message):
    """Handle incoming voice messages — STT → process as text → reply with voice."""
    uid = message.from_user.id
    if check_rate_limit(uid):
        await message.answer("⏳ Слишком много сообщений. Подожди минуту и попробуй снова.")
        return
    await bot.send_chat_action(message.chat.id, "record_voice")
    
    try:
        # Download voice file
        file = await bot.get_file(message.voice.file_id)
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}"
        loop = asyncio.get_event_loop()
        req = urllib.request.Request(file_url)
        resp = await loop.run_in_executor(None, lambda: urllib.request.urlopen(req, timeout=15))
        ogg_bytes = resp.read()
        
        # STT
        user_text = await speech_to_text(ogg_bytes)
        if not user_text:
            await message.answer("🎤 Не удалось распознать голосовое сообщение. Попробуйте ещё раз или напишите текстом.")
            return
        
        logger.info(f"Voice from {message.from_user.id}: {user_text[:100]}")
        
        # Process as if it was a text message — inject text and call on_text logic
        message.text = user_text
        await on_text(message)
        
    except Exception as e:
        logger.error(f"Voice handler error: {e}")
        await message.answer("😔 Ошибка обработки голосового сообщения. Попробуйте написать текстом.")


@router.message(F.photo)
async def on_photo(message: types.Message):
    """Handle screenshots — analyze with Gemini Vision and guide the user."""
    uid = message.from_user.id
    if check_rate_limit(uid):
        await message.answer("⏳ Слишком много сообщений.")
        return

    await bot.send_chat_action(message.chat.id, "typing")
    session = get_session(uid)
    lang = session.get("lang", "ru")
    caption = message.caption or ""

    try:
        # Download the largest photo
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}"
        loop = asyncio.get_event_loop()
        req_obj = urllib.request.Request(file_url)
        resp = await loop.run_in_executor(None, lambda: urllib.request.urlopen(req_obj, timeout=15))
        img_bytes = resp.read()

        import base64
        img_b64 = base64.b64encode(img_bytes).decode()

        # Determine context
        if session.get("awaiting_bot_token") or session.get("onboarding"):
            context = "Клиент настраивает AI-ассистента и прислал скриншот. Помоги разобраться что на экране и подскажи куда нажать / что делать дальше."
        elif caption:
            context = f"Клиент прислал скриншот с подписью: «{caption}». Помоги разобраться."
        else:
            context = "Клиент прислал скриншот. Проанализируй что на нём и подскажи что делать — куда нажать, что ввести, какой следующий шаг."

        # Call Gemini Vision
        vision_url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_KEY}"
        vision_payload = {
            "contents": [{
                "parts": [
                    {"text": f"""Ты — AI-консультант AI Centers. {context}

ПРАВИЛА:
- Отвечай коротко и конкретно (2-5 предложений)
- Покажи ТОЧНО куда нажать (опиши кнопку/элемент)
- Если видишь ошибку — объясни как исправить
- Отвечай на {'русском' if lang == 'ru' else 'английском'} языке
- Используй HTML теги (<b>, <i>) умеренно"""},
                    {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}}
                ]
            }],
            "generationConfig": {"maxOutputTokens": 1024, "temperature": 0.3}
        }

        import json as _json
        req_data = _json.dumps(vision_payload).encode()
        vision_req = urllib.request.Request(vision_url, data=req_data, headers={"Content-Type": "application/json"})
        vision_resp = await loop.run_in_executor(None, lambda: urllib.request.urlopen(vision_req, timeout=30))
        result = _json.loads(vision_resp.read().decode())

        reply = result["candidates"][0]["content"]["parts"][0]["text"].strip()
        await message.answer(reply, parse_mode="HTML")

        # Save to history
        session["history"].append({"role": "user", "parts": [f"[Скриншот] {caption}"]})
        session["history"].append({"role": "model", "parts": [reply]})

        logger.info(f"Photo analyzed for {uid}: {reply[:100]}")

    except Exception as e:
        logger.error(f"Photo handler error: {e}")
        await message.answer("📸 Вижу скриншот! Опишите текстом что именно не получается, и я подскажу пошагово.")


@router.message(F.text)
async def on_text(message: types.Message):
    uid = message.from_user.id
    session = get_session(uid)
    text = message.text

    # Rate limiting
    if check_rate_limit(uid):
        await message.answer("⏳ Слишком много сообщений. Подожди минуту и попробуй снова.")
        return

    # Prompt injection guard
    if detect_injection(text):
        logger.warning(f"Prompt injection attempt from {uid}: {text[:200]}")
        await message.answer("🛡️ Некорректный запрос. Давай общаться нормально — спроси что тебя интересует!")
        return

    # ── Onboarding text input ──
    if session.get("onboarding"):
        step = session.get("onboarding_step", 0)
        if step == 2:
            # Step 2: got business name → ask tasks
            from core import get_plan_total_steps
            total = get_plan_total_steps(session.get("plan", "starter"))
            session["ob_biz_name"] = text.strip()
            session["onboarding_step"] = 3
            await message.answer(
                f"✅ Компания: <b>{text.strip()}</b>\n\n"
                f"📋 <b>Шаг 3 из {total} — Задачи ассистента</b>\n\n"
                f"Что должен делать ваш AI-ассистент?\n"
                f"Например: <i>Отвечать на вопросы клиентов, принимать заказы, записывать на приём, рассказывать о ценах</i>",
            )
            return
        elif step == 3:
            # Step 3: got tasks → ask channel
            from core import get_plan_total_steps
            total = get_plan_total_steps(session.get("plan", "starter"))
            session["ob_tasks"] = text.strip()
            session["onboarding_step"] = 4
            ch_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📱 Telegram", callback_data="ob_channel_telegram"),
                 InlineKeyboardButton(text="💬 WhatsApp", callback_data="ob_channel_whatsapp")],
                [InlineKeyboardButton(text="🌐 Сайт", callback_data="ob_channel_website"),
                 InlineKeyboardButton(text="🔗 Все каналы", callback_data="ob_channel_all")],
            ])
            await message.answer(
                f"✅ Задачи: <b>{text.strip()[:100]}</b>\n\n"
                f"📋 <b>Шаг 4 из {total} — Где подключить?</b>\n\n"
                f"В каком канале будет работать ваш AI-ассистент?",
                reply_markup=ch_kb,
            )
            return
        elif step == 5:
            # Step 5: Voice Secretary — got phone number
            session["ob_voice_phone"] = text.strip()
            from core import get_plan_total_steps
            from handlers.payments import get_plan_features
            total = get_plan_total_steps(session.get("plan", "starter"))
            features = get_plan_features(session.get("plan", "starter"))

            if features.get("crm"):
                session["onboarding_step"] = 6
                crm_kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="AmoCRM", callback_data="ob_crm_amocrm"),
                     InlineKeyboardButton(text="Bitrix24", callback_data="ob_crm_bitrix")],
                    [InlineKeyboardButton(text="HubSpot", callback_data="ob_crm_hubspot"),
                     InlineKeyboardButton(text="Google Sheets", callback_data="ob_crm_gsheets")],
                    [InlineKeyboardButton(text="🚫 Пока без CRM", callback_data="ob_crm_skip")],
                ])
                await message.answer(
                    f"✅ Телефон: <b>{text.strip()}</b>\n\n"
                    f"📋 <b>Шаг 6 из {total} — CRM интеграция</b>\n\n"
                    f"📊 Какую CRM-систему вы используете?\n"
                    f"AI-ассистент будет автоматически заносить данные клиентов.",
                    reply_markup=crm_kb,
                )
            else:
                # No CRM → go to data collection
                session["onboarding_step"] = 0
                session["onboarding"] = False
                session["awaiting_data"] = True
                await _show_data_collection(message, session)
            return
    
    # ── Awaiting bot token from BotFather ──
    if session.get("awaiting_bot_token"):
        # Help request — AI support (no human escalation)
        help_words = {"помощь", "помоги", "help", "не получается", "не могу", "не понимаю", "сложно"}
        if text.lower().strip().rstrip("!.?") in help_words or "помо" in text.lower():
            await message.answer(
                "💡 <b>Помогаю!</b>\n\n"
                "Вот подробная инструкция — это займёт 1 минуту:\n\n"
                "1️⃣ Откройте Telegram → в поиске напишите <b>BotFather</b>\n"
                "2️⃣ Нажмите на него → <b>Start</b>\n"
                "3️⃣ Напишите /newbot\n"
                "4️⃣ Он спросит имя — напишите название вашего бизнеса\n"
                "5️⃣ Он спросит username — придумайте уникальное, на конце <b>_bot</b>\n"
                "   Например: <code>moy_restoran_bot</code>\n"
                "6️⃣ Появится длинный код — это <b>токен</b>\n\n"
                "📸 <i>Не получается? Скиньте скриншот — подскажу!</i>\n"
                "7️⃣ Нажмите на него чтобы скопировать\n"
                "8️⃣ Вставьте сюда 👇\n\n"
                "Если что-то пойдёт не так — просто напишите что именно, и я помогу!",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🤖 Открыть @BotFather", url="https://t.me/BotFather")],
                ]),
            )
            return

        import re as _re2
        token_match = _re2.search(r'\d{8,}:[A-Za-z0-9_-]{30,}', text)
        if token_match:
            bot_token = token_match.group(0)
            session["awaiting_bot_token"] = False
            session["bot_token"] = bot_token

            await message.answer("⏳ <b>Проверяю токен и создаю бота...</b>")

            # Call engine API to create the bot
            biz_name = session.get("ob_biz_name", "Мой бизнес")
            niche = session.get("ob_niche_name", "бизнес")
            tasks = session.get("ob_tasks", "")
            training = session.get("ob_training_data", [])
            knowledge = "\n".join([d.get("text", "") for d in training])

            try:
                import aiohttp
                # First register/login user to get JWT
                async with aiohttp.ClientSession() as http:
                    # Try auto-setup with URL if available, otherwise create from text
                    url_data = [d["text"] for d in training if d.get("type") == "url"]
                    
                    if url_data:
                        payload = {
                            "bot_token": bot_token,
                            "url": url_data[0],
                            "business_type": niche,
                            "language": session.get("lang", "ru"),
                        }
                        endpoint = f"{ENGINE_API_URL}/internal/auto-setup"
                    else:
                        payload = {
                            "bot_token": bot_token,
                            "name": biz_name,
                            "description": f"{niche}. {tasks}",
                            "tone": "дружелюбный, профессиональный",
                            "knowledge_base": f"Бизнес: {biz_name}\nНиша: {niche}\nЗадачи: {tasks}\n\n{knowledge}",
                        }
                        endpoint = f"{ENGINE_API_URL}/internal/create-bot"

                    resp = await http.post(
                        endpoint,
                        json=payload,
                        headers={"X-Internal-Key": PLATFORM_API_KEY},
                        timeout=aiohttp.ClientTimeout(total=60),
                    )
                    result = await resp.json()

                if resp.status in (200, 201):
                    bot_username = result.get("bot_username", "")
                    session["created_bot_username"] = bot_username
                    kb = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text=f"🤖 Открыть @{bot_username}", url=f"https://t.me/{bot_username}")] if bot_username else [],
                        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_menu")],
                    ])
                    # Message 1: Success
                    await message.answer(
                        f"🎉 <b>Ваш AI-ассистент создан!</b>\n\n"
                        f"🤖 Бот: @{bot_username}\n"
                        f"🏢 {biz_name}\n\n"
                        f"✅ Бот уже запущен и готов общаться с клиентами!",
                    )

                    # Message 2: Check your bot
                    await message.answer(
                        f"✅ <b>Шаг 1 — Проверьте бота</b>\n\n"
                        f"Откройте @{bot_username} и напишите что-нибудь.\n"
                        f"Проверьте, как AI отвечает клиентам.",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text=f"🤖 Открыть @{bot_username}", url=f"https://t.me/{bot_username}")],
                        ]),
                    )

                    # Message 3: Connection options
                    connect_kb = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="📱 Telegram", callback_data="guide_telegram")],
                        [InlineKeyboardButton(text="💬 WhatsApp", callback_data="guide_whatsapp")],
                        [InlineKeyboardButton(text="🌐 Сайт", callback_data="guide_website")],
                        [InlineKeyboardButton(text="📸 Instagram", callback_data="guide_instagram")],
                        [InlineKeyboardButton(text="📝 Доработать бота", callback_data="ob_customize_bot")],
                        [InlineKeyboardButton(text="📊 Статистика", callback_data="ob_bot_stats")],
                        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_menu")],
                    ])

                    await message.answer(
                        f"⚡ <b>Шаг 2 — Подключите бота к вашим каналам</b>\n\n"
                        f"Выберите куда хотите подключить @{bot_username}:\n\n"
                        f"📱 <b>Telegram</b> — бот в группе, канале или бизнес-аккаунте\n"
                        f"💬 <b>WhatsApp</b> — бот отвечает клиентам в WhatsApp\n"
                        f"🌐 <b>Сайт</b> — виджет чата на вашем сайте\n"
                        f"📸 <b>Instagram</b> — автоответы в Direct\n\n"
                        f"Можно подключить сразу несколько! 👇",
                        reply_markup=connect_kb,
                    )

                    # Message 4: Support reminder
                    await message.answer(
                        f"💬 <b>Поддержка 24/7</b>\n\n"
                        f"Этот чат — ваша линия поддержки.\n\n"
                        f"Вы можете в любой момент написать сюда:\n"
                        f"• Вопросы по работе бота\n"
                        f"• Как обучить бота новым данным\n"
                        f"• Как изменить ответы или стиль\n"
                        f"• Как подключить к другим каналам\n"
                        f"• Любые технические вопросы\n\n"
                        f"Просто напишите — AI-поддержка ответит мгновенно! 🚀",
                    )

                    try:
                        await bot.send_message(ADMIN_ID,
                            f"✅ <b>БОТ СОЗДАН!</b>\n"
                            f"👤 {message.from_user.full_name}\n"
                            f"🤖 @{bot_username}\n"
                            f"🏢 {biz_name}")
                    except Exception: pass
                else:
                    error = result.get("detail", "Unknown error")
                    await message.answer(
                        f"❌ Ошибка: {error}\n\n"
                        f"Попробуйте другой токен или напишите «помощь».",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="🤖 Открыть @BotFather", url="https://t.me/BotFather")],
                            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_menu")],
                        ]),
                    )
                    session["awaiting_bot_token"] = True  # Let them retry
            except Exception as e:
                logger.error(f"Engine API error: {e}")
                await message.answer(
                    f"⚠️ Сервис временно недоступен. Мы сохранили ваши данные и создадим бота в ближайшее время.\n\n"
                    f"Токен получен ✅",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_menu")],
                    ]),
                )
                try:
                    await bot.send_message(ADMIN_ID,
                        f"⚠️ ENGINE API FAIL\n{message.from_user.full_name}\nToken: {bot_token[:20]}...\nError: {e}")
                except Exception: pass
            return
        else:
            await message.answer(
                "🤔 Это не похоже на токен бота.\n\n"
                "Токен выглядит так:\n<code>1234567890:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw</code>\n\n"
                "Скопируйте его из @BotFather и отправьте сюда.",
            )
            return

    # ── Awaiting channel tokens (WhatsApp/Instagram/Wazzup/Twilio) ──
    channel_awaiting = None
    if session.get("awaiting_wazzup_key"):
        channel_awaiting = "wazzup"
    elif session.get("awaiting_wa_token"):
        channel_awaiting = "meta_wa"
    elif session.get("awaiting_twilio_token"):
        channel_awaiting = "twilio"
    elif session.get("awaiting_ig_token"):
        channel_awaiting = "meta_ig"

    if channel_awaiting:
        token_text = text.strip()
        if len(token_text) < 10:
            await message.answer(
                "🤔 Это слишком короткий ключ. Проверьте и попробуйте ещё раз.",
            )
            return

        # Save channel credentials
        if "channel_credentials" not in session:
            session["channel_credentials"] = {}
        session["channel_credentials"][channel_awaiting] = token_text

        # Clear awaiting flags
        for flag in ["awaiting_wazzup_key", "awaiting_wa_token", "awaiting_twilio_token", "awaiting_ig_token"]:
            session.pop(flag, None)

        bot_username = session.get("created_bot_username", "")
        biz_name = session.get("ob_biz_name", "")
        uid = message.from_user.id
        user = message.from_user

        channel_names = {
            "wazzup": "Wazzup24 (WhatsApp + Instagram)",
            "meta_wa": "Meta WhatsApp API",
            "twilio": "Twilio WhatsApp",
            "meta_ig": "Meta Instagram API",
        }
        ch_display = channel_names.get(channel_awaiting, channel_awaiting)

        # Auto-configure via Engine API
        await message.answer("⏳ <b>Проверяю и подключаю...</b>")

        try:
            import aiohttp
            async with aiohttp.ClientSession() as http:
                payload = {
                    "bot_username": bot_username,
                    "channel_type": channel_awaiting,
                    "credentials": token_text,
                    "user_id": uid,
                }
                resp = await http.post(
                    f"{ENGINE_API_URL}/channels/connect",
                    json=payload,
                    headers={"X-Internal-Key": PLATFORM_API_KEY},
                    timeout=aiohttp.ClientTimeout(total=30),
                )
                if resp.status in (200, 201):
                    result = await resp.json()
                    await message.answer(
                        f"✅ <b>{ch_display} подключён!</b>\n\n"
                        f"🤖 Бот @{bot_username} теперь отвечает клиентам через {ch_display}.\n\n"
                        f"Хотите подключить ещё каналы?",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="🔌 Другие каналы", callback_data="guide_back")],
                            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_menu")],
                        ]),
                    )
                else:
                    error_data = await resp.json()
                    error_msg = error_data.get("detail", "Неизвестная ошибка")
                    await message.answer(
                        f"❌ Не удалось подключить: {error_msg}\n\n"
                        f"Проверьте данные и попробуйте ещё раз.",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="🔄 Попробовать снова", callback_data=f"guide_whatsapp")],
                            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_menu")],
                        ]),
                    )
        except Exception as e:
            logger.error(f"Channel connect error: {e}")
            # Fallback: save for manual processing
            await message.answer(
                f"✅ <b>Данные получены!</b>\n\n"
                f"📱 Канал: {ch_display}\n"
                f"🔗 Подключаем к @{bot_username}...\n\n"
                f"Настройка занимает до 5 минут. Мы пришлём уведомление когда всё будет готово!",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔌 Другие каналы", callback_data="guide_back")],
                    [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_menu")],
                ]),
            )

        # Notify admin
        try:
            if uid != ADMIN_ID:
                await bot.send_message(ADMIN_ID,
                    f"🔌 <b>ПОДКЛЮЧЕНИЕ КАНАЛА</b>\n\n"
                    f"👤 {user.full_name}{(' (@' + user.username + ')') if user.username else ''}\n"
                    f"📱 {ch_display}\n"
                    f"🤖 @{bot_username}\n"
                    f"🔑 {token_text[:30]}...")
        except Exception: pass
        return

    # ── Awaiting training data (post-onboarding) ──
    if session.get("awaiting_data"):
        data_type = session.get("awaiting_data", True)
        # Save the data
        if "ob_training_data" not in session:
            session["ob_training_data"] = []
        session["ob_training_data"].append({"type": str(data_type), "text": text.strip()})

        niche_key = session.get("ob_niche", "other")
        biz_name = session.get("ob_biz_name", "Мой бизнес")

        type_labels = {"url": "🌐 Ссылка", "menu": "🍽 Меню", "price": "📄 Прайс", "desc": "📝 Описание", "catalog": "🛍 Каталог"}
        label = type_labels.get(data_type, "📎 Данные")

        count = len(session["ob_training_data"])

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📎 Добавить ещё данные", callback_data="ob_more_data")],
            [InlineKeyboardButton(text="✅ Готово — создать бота!", callback_data="ob_create_bot")],
        ])

        await message.answer(
            f"✅ {label} получено!\n\n"
            f"📊 Собрано материалов: <b>{count}</b>\n\n"
            f"Можете отправить ещё (фото, файлы, ссылки, текст) или нажмите «Создать бота».",
            reply_markup=kb,
        )

        # Notify admin
        user = message.from_user
        try:
            if uid != ADMIN_ID:
                await bot.send_message(ADMIN_ID,
                    f"📎 Данные от клиента {user.full_name} ({biz_name}):\n"
                    f"{label}: {text.strip()[:500]}")
        except Exception: pass
        return

    # === Mode: custom assistant chat ===
    if session["mode"] == "assistant" and session["persona"]:
        session["count"] += 1
        remaining = FREE_LIMIT - session["count"]
        
        if remaining <= 0 and not is_paid(uid) and not session.get("sales_mode"):
            session["sales_mode"] = True
            session["mode"] = "sales"
            
            sales_intro = gemini_chat(
                SYSTEM_PROMPT + "\n\nСЕЙЧАС РЕЖИМ ПРОДАЖИ. Клиент только что исчерпал 20 бесплатных сообщений с AI-помощником. "
                f"Его помощник: {session['persona']}. "
                "Мягко скажи что бесплатные сообщения кончились, похвали выбор, предложи продолжить оплатив через Telegram Stars. "
                "Скажи что неделя всего 150 ⭐, а месяц 500 ⭐ — и кнопки оплаты уже внизу.",
                session["history"],
                f"[Система: пользователь исчерпал лимит. Последнее сообщение: {text}]"
            )
            session["history"].append({"user": text, "bot": sales_intro})
            
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⭐ Неделя — 150 Stars", callback_data="pay_week")],
                [InlineKeyboardButton(text="⭐ Месяц — 500 Stars (выгодно!)", callback_data="pay_month")],
                [InlineKeyboardButton(text="👑 Премиум — 1500 Stars", callback_data="pay_premium")],
                [InlineKeyboardButton(text="💬 Связаться с @timurtokazov", url="https://t.me/timurtokazov")],
            ])
            await message.answer(sales_intro, reply_markup=kb)
            
            # Notify admin
            user = message.from_user
            try:
                await bot.send_message(ADMIN_ID,
                    f"🔥 <b>Горячий лид!</b>\n"
                    f"👤 {user.full_name}{(' (@' + user.username + ')') if user.username else ''}\n"
                    f"🆔 {user.id}\n"
                    f"📝 Помощник: {session['persona'][:200]}\n"
                    f"💬 {session['count']} сообщений использовано\n"
                    f"⭐ Кнопки оплаты Stars отправлены")
            except Exception: pass
            return
        
        # Paid user — no limit
        if is_paid(uid):
            remaining = 999
        
        # Normal assistant chat
        system = ASSISTANT_SYSTEM.format(persona=session["persona"])
        response = gemini_chat(system, session["history"], text)
        session["history"].append({"user": text, "bot": response})
        
        if remaining <= 5 and remaining > 0:
            response += f"\n\n<i>💬 Осталось {remaining} сообщений</i>"
        
        await send_with_voice(message, response)
        return
    
    # === Mode: sales (after limit) ===
    if session.get("mode") == "sales":
        sales_prompt = (
            SYSTEM_PROMPT + "\n\nРЕЖИМ ПРОДАЖИ. Клиент исчерпал бесплатный лимит. "
            f"Его помощник был: {session.get('persona', 'не указан')}. "
            "Отвечай на вопросы о ценах, тарифах. Будь дружелюбным, не дави. "
            "Если хочет оплатить — дай ссылку на сайт aicenters.co или скажи написать @timurtokazov. "
            "Если хочет помощника под ключ ($499+) — тоже направь к @timurtokazov."
        )
        response = gemini_chat(sales_prompt, session["history"], text)
        session["history"].append({"user": text, "bot": response})
        await send_with_voice(message, response)
        return
    
    # === Mode: objection handler (sales funnel Q&A) ===
    if session.get("mode") == "objection_handler":
        lang = session.get("lang", "ru")
        lang_instruction = {"ru": "Отвечай на русском.", "en": "Answer in English.", "ka": "უპასუხე ქართულად.", "tr": "Türkçe cevap ver.", "kk": "Қазақша жауап бер.", "uz": "O'zbekcha javob ber."}
        objection_prompt = (
            SYSTEM_PROMPT + f"\n\nРЕЖИМ ОБРАБОТКИ ВОЗРАЖЕНИЙ. "
            f"{lang_instruction.get(lang, 'Answer in English.')} "
            "Клиент интересуется AI-ассистентом для бизнеса, но задаёт вопросы перед покупкой. "
            "Отвечай коротко (2-4 предложения), конкретно, с фактами. "
            "В конце ответа мягко верни к действию."
        )
        response = gemini_chat(objection_prompt, session["history"], text)
        session["history"].append({"user": text, "bot": response})

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "btn_try_free").split("(")[0].strip(), callback_data="funnel_demo")],
            [InlineKeyboardButton(text=t(lang, "btn_pricing"), callback_data="funnel_pricing")],
            [InlineKeyboardButton(text=t(lang, "btn_more_question"), callback_data="funnel_question")],
        ])
        await message.answer(response, reply_markup=kb)
        return

    # === Computer Use pilot/demo flow ===
    if await _get_handle_cu_text()(message, session):
        return

    # === Funnel gate: always show funnel before Gemini ===
    if not session.get("funnel_shown"):
        return await _get_show_funnel_step1()(message)

    # === Mode: receptionist (default) ===
    response = gemini_chat(SYSTEM_PROMPT, session["history"], text)
    session["history"].append({"user": text, "bot": response})
    
    # Check for payment markers [PAY:week/month/premium/custom]
    import re as _re
    pay_match = _re.search(r'\[PAY:(\w+)\]', response)
    if pay_match:
        plan_key = pay_match.group(1)
        clean_resp = _re.sub(r'\[PAY:\w+\]', '', response).strip()
        if clean_resp:
            await message.answer(clean_resp)
        if plan_key in STAR_PLANS:
            await _get_send_stars_invoice()(message, plan_key)
        session["history"].append({"user": text, "bot": clean_resp})
        return
    
    # Check if receptionist wants to create an assistant
    if "[CREATE_ASSISTANT:" in response or "[CREATE_ASSISTANT]" in response:
        # Extract persona description
        import re
        match = re.search(r'\[CREATE_ASSISTANT[:\s]*([^\]]*)\]', response)
        if match and match.group(1).strip():
            persona = match.group(1).strip()
        else:
            persona = text  # use user's message as persona
        
        # Clean the marker from response
        clean_response = re.sub(r'\[CREATE_ASSISTANT[:\s]*[^\]]*\]', '', response).strip()
        
        session["persona"] = persona
        session["mode"] = "assistant"
        session["count"] = 0
        session["history"] = []  # fresh history for assistant
        
        # Generate first assistant response
        system = ASSISTANT_SYSTEM.format(persona=persona)
        greeting = gemini_chat(system, [], "Привет! Представься и предложи помощь. 2-3 предложения.")
        session["history"].append({"user": "Привет", "bot": greeting})
        session["count"] = 1
        
        if clean_response:
            await message.answer(clean_response)
        await message.answer(f"{'—' * 15}\n{greeting}\n{'—' * 15}\n\n<i>💬 {FREE_LIMIT - 1} бесплатных сообщений</i>")
        
        # Notify admin
        user = message.from_user
        try:
            await bot.send_message(ADMIN_ID,
                f"🆕 <b>Новый AI-помощник!</b>\n"
                f"👤 {user.full_name}{(' (@' + user.username + ')') if user.username else ''}\n"
                f"📝 {persona[:300]}")
        except Exception: pass
        
        logger.info(f"Created assistant for {uid}: {persona[:100]}")
    else:
        # Add action buttons after every AI response
        action_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "btn_order_assistant"), callback_data="funnel_pricing")],
            [InlineKeyboardButton(text="🎯 Демо", callback_data="funnel_demo"),
             InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_menu")],
        ])
        await send_with_voice(message, response, reply_markup=action_kb)



# ══════════════════════════════════════════
# ONBOARDING FLOW (after payment)
# ══════════════════════════════════════════

# Step 1: Business niche selected
