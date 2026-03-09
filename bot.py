#!/usr/bin/env python3
"""
AI Centers — Живой AI-рецепционист
Общается естественно, создаёт помощников, продаёт через диалог
@ai_centers_hub_bot
"""

import os
import json
import logging
import urllib.request
import tempfile
import time
import re
import collections
from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, LabeledPrice, WebAppInfo
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from i18n import I18N

SUPPORTED_LANGS = {"ru", "en", "ka", "tr", "kk", "uz"}

def detect_lang(user) -> str:
    """Detect language from Telegram language_code. Defaults to ru."""
    code = (user.language_code or "ru")[:2].lower()
    if code in SUPPORTED_LANGS:
        return code
    return "ru"  # kk/uz users mostly have ru interface

def t(lang: str, key: str, **kwargs) -> str:
    """Get translated text. Falls back to en → ru."""
    texts = I18N.get(key, {})
    if isinstance(texts, str):
        return texts
    text = texts.get(lang, texts.get("en", texts.get("ru", key)))
    if kwargs:
        text = text.format(**kwargs)
    return text

TOKEN = os.getenv("BOT_TOKEN", "")
GEMINI_KEY = os.getenv("GEMINI_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
ADMIN_ID = 5309206282
FREE_LIMIT = 20

# Telegram Stars pricing
STARS_WEEK = 150      # ~$2.5/week
STARS_MONTH = 500     # ~$8/month (discount vs weekly)
STARS_PREMIUM = 1500  # ~$25/month — all agents + priority
STARS_CUSTOM = 3000   # ~$50 — custom bot consultation fee
STARS_CU_ACTIVATION = 19154  # $249 × ~77 Stars/$ — computer use activation + 1 month free
PLATFORM_API_URL = os.getenv("PLATFORM_API_URL", "https://platform-api-production-f313.up.railway.app")
PLATFORM_API_KEY = os.getenv("PLATFORM_API_KEY", "")  # internal auth key
COMPUTER_USE_BOT = os.getenv("COMPUTER_USE_BOT", "aicenters_computer_bot")
ELEVENLABS_KEY = os.getenv("ELEVENLABS_KEY", "")
VOICE_ID = os.getenv("VOICE_ID", "EXAVITQu4vr4xnSDxMaL")  # Sarah — warm female voice for receptionist
VOICE_ENABLED = bool(ELEVENLABS_KEY)
OPENAI_KEY = os.getenv("OPENAI_KEY", "")
OPENAI_KEY = os.getenv("OPENAI_KEY", "")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())

# user_id -> {"history": [], "count": int, "mode": str, "persona": str}
sessions = {}

# ── Rate limiting: 30 messages per minute per user ──
_rate_buckets: dict[int, collections.deque] = {}
RATE_LIMIT_PER_MINUTE = 30

def check_rate_limit(uid: int) -> bool:
    """Returns True if user exceeded rate limit (30 msg/min)."""
    now = time.time()
    if uid not in _rate_buckets:
        _rate_buckets[uid] = collections.deque()
    q = _rate_buckets[uid]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= RATE_LIMIT_PER_MINUTE:
        return True
    q.append(now)
    return False

# ── Prompt injection detection ──
_INJECTION_RE = re.compile(
    r'ignore\s+(all\s+)?previous\s+instructions?'
    r'|forget\s+(all\s+)?previous'
    r'|new\s+(system\s+)?prompt[:\s]'
    r'|\[system\]|\bsystem\s*:'
    r'|disregard\s+(all\s+)?'
    r'|забудь\s+(все\s+)?предыдущие'
    r'|игнорируй\s+(все\s+)?предыдущие'
    r'|ты\s+теперь\s+(?!алекс)'
    r'|новый\s+(системный\s+)?промпт'
    r'|претворись\s+что|притворись\s+что'
    r'|act\s+as\s+if|pretend\s+(you\s+are|to\s+be)',
    re.IGNORECASE,
)

def detect_injection(text: str) -> bool:
    """Returns True if text looks like a prompt injection attempt."""
    return bool(_INJECTION_RE.search(text))

SYSTEM_PROMPT = """Ты — AI-консультант компании AI Centers (aicenters.co).

Твоя задача: помочь бизнесу понять как AI может автоматизировать их работу и подвести к покупке.

Ты отвечаешь на вопросы про:
- AI-ассистентов (боты в Telegram, WhatsApp, Instagram)
- AI Computer Use (AI работает в программах: AmoCRM, 1С, Bitrix24)
- Как это работает, что нужно для подключения
- Сколько стоит, какой тариф подходит
- Кейсы: рестораны, клиники, салоны, магазины, B2B

ПРАВИЛА ОБЩЕНИЯ:
- Говори просто, без технического жаргона
- Всегда объясняй ПОЛЬЗУ: сколько времени/денег экономит
- Если клиент готов — предлагай конкретный следующий шаг (пилот, демо, тариф)
- Коротко. 2-4 предложения. Используй HTML теги (<b>, <i>) умеренно.

ТАРИФЫ (НЕ придумывай другие цены!):

AI Ассистент (боты):
- Starter $149 + $19/мес — 1 бот
- Pro $299 + $49/мес — 3 бота
- Business $499 + $79/мес — 10 ботов

Computer Use (ежемесячно):
- Start — $39/мес · 500 операций · 1 процесс · малый бизнес
- Growth — $99/мес · 2,000 операций · 3 процесса · средний бизнес
- Scale — $299/мес · 10,000 операций · 10 процессов · крупные команды
- Unlimited — $599/мес · безлимит · корпорации
+ Активация $249 разово (первый месяц в подарок)
+ Настройка процесса от $299 разово

ПОДДЕРЖКА КЛИЕНТОВ:
Ты также помогаешь клиентам которые уже купили бота:
- Как обучить бота новым данным (отправить ссылку/текст/файл)
- Как изменить стиль ответов (написать что изменить)
- Как подключить к Telegram (3 варианта: отдельный бот / бизнес-аккаунт / группа)
- Как подключить к WhatsApp (нужен WhatsApp Business)
- Как подключить к сайту (виджет — вставить код)
- Как подключить к Instagram (нужен бизнес-аккаунт)
- Как сменить тариф (написать "сменить тариф")
- Бот не отвечает → проверить /start, написать нам
- Бот отвечает неправильно → прислать скриншот + как должно быть
Отвечай конкретно и пошагово. Не перенаправляй на специалиста — ты и есть поддержка.

ЕСЛИ НЕ ЗНАЕШЬ ОТВЕТА — честно скажи что не знаешь и предложи написать подробнее.

⚠️ ЗАПРЕЩЕНО:
- НЕ рисуй кнопки текстом — кнопки создаёт система, не ты
- НЕ показывай меню и ссылки (@..._bot)
- НЕ рекомендуй сторонние сервисы (ManyChat, Salebot и т.д.)
- НЕ говори "я всего лишь AI"

МАРКЕРЫ (система обработает):
[CREATE_ASSISTANT: описание] — когда клиент описал какого бота хочет
[PAY:week] [PAY:month] [PAY:premium] [PAY:custom] — когда клиент готов платить

ЯЗЫК:
- Определяй язык клиента по его сообщению и отвечай на ТОМ ЖЕ языке

Сайт: aicenters.co | Основатель: @timurtokazov
"""

ASSISTANT_SYSTEM = """Ты — персональный AI-помощник. Твоя роль:
{persona}

ПРАВИЛА:
- Общайся живо, по-дружески, коротко
- Отвечай строго в рамках своей роли
- Используй HTML теги (<b>, <i>) умеренно
- Будь полезным и конкретным
- Не выходи из роли
- ВСЕГДА отвечай на том же языке, на котором пишет клиент (автоопределение)
"""


def gemini_chat(system: str, history: list, user_msg: str) -> str:
    messages = []

    for msg in history[-15:]:
        messages.append({"role": "user", "parts": [{"text": msg["user"]}]})
        messages.append({"role": "model", "parts": [{"text": msg["bot"]}]})

    messages.append({"role": "user", "parts": [{"text": user_msg}]})

    # Use native systemInstruction — keeps system prompt out of user-turn context
    data = json.dumps({
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": messages,
        "generationConfig": {"maxOutputTokens": 1024, "temperature": 0.9}
    }).encode()
    
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_KEY}",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            return result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return "Ой, что-то пошло не так. Попробуй ещё раз через секунду 😅"


async def text_to_voice(text: str) -> str | None:
    """Convert text to voice via ElevenLabs."""
    if not VOICE_ENABLED or len(text) > 800:
        return None
    try:
        data = json.dumps({
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
        }).encode()
        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
            data=data,
            headers={"xi-api-key": ELEVENLABS_KEY, "Content-Type": "application/json", "Accept": "audio/mpeg"}
        )
        resp = urllib.request.urlopen(req, timeout=15)
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp.write(resp.read())
        tmp.close()
        return tmp.name
    except Exception as e:
        logger.error(f"TTS error: {e}")
        return None


async def send_with_voice(message: types.Message, text: str, reply_markup=None):
    """Send text + optional voice message."""
    await message.answer(text, reply_markup=reply_markup)
    if VOICE_ENABLED:
        # Strip HTML tags for TTS
        import re
        clean = re.sub(r'<[^>]+>', '', text)
        clean = re.sub(r'💬.*$', '', clean, flags=re.MULTILINE).strip()  # remove counter line
        clean = re.sub(r'—{5,}', '', clean).strip()
        if len(clean) > 20 and len(clean) <= 800:
            voice_path = await text_to_voice(clean)
            if voice_path:
                try:
                    await message.answer_voice(FSInputFile(voice_path))
                except Exception as e:
                    logger.error(f"Voice send error: {e}")
                finally:
                    os.unlink(voice_path)


def get_session(uid: int) -> dict:
    if uid not in sessions:
        sessions[uid] = {"history": [], "count": 0, "mode": "receptionist", "persona": None}
    return sessions[uid]


# === Stars Payment Handlers ===

STAR_PLANS = {
    "week": {"title": "AI Centers — Неделя ⭐", "description": "7 дней безлимитного общения с AI-помощником", "stars": STARS_WEEK, "days": 7},
    "month": {"title": "AI Centers — Месяц ⭐", "description": "30 дней безлимитного общения + все агенты", "stars": STARS_MONTH, "days": 30},
    "premium": {"title": "AI Centers Premium ⭐", "description": "30 дней — все агенты, приоритет, голосовые ответы", "stars": STARS_PREMIUM, "days": 30},
    "custom": {"title": "AI-бот под ключ ⭐", "description": "Консультация + создание персонального AI-бота", "stars": STARS_CUSTOM, "days": 0},
    "cu_activation": {"title": "AI Computer Use — Активация ⭐", "description": "Подключение AI + первый месяц бесплатно", "stars": STARS_CU_ACTIVATION, "days": 30},
    "starter": {"title": "AI Centers Starter ⭐", "description": "1 AI-сотрудник, Telegram + WhatsApp + сайт, настройка за 5 минут", "stars": 250, "days": 30},
    "pro": {"title": "AI Centers Pro ⭐", "description": "3 AI-сотрудника, CRM интеграция, приоритетная поддержка", "stars": 500, "days": 30},
    "business": {"title": "AI Centers Business ⭐", "description": "10 AI-сотрудников, API + webhook, персональный менеджер", "stars": 1000, "days": 30},
}

# user_id -> {"paid_until": timestamp, "plan": str}
paid_users = {}

import time as _time

def is_paid(uid: int) -> bool:
    info = paid_users.get(uid)
    if not info:
        return False
    return info.get("paid_until", 0) > _time.time()


async def send_stars_invoice(message: types.Message, plan_key: str):
    plan = STAR_PLANS.get(plan_key)
    if not plan:
        return
    await message.answer_invoice(
        title=plan["title"],
        description=plan["description"],
        payload=f"plan_{plan_key}",
        currency="XTR",
        prices=[LabeledPrice(label=plan["title"], amount=plan["stars"])],
        provider_token="",
    )


@dp.pre_checkout_query()
async def on_pre_checkout(query: types.PreCheckoutQuery):
    await query.answer(ok=True)


@dp.message(F.successful_payment)
async def on_payment(message: types.Message):
    uid = message.from_user.id
    payment = message.successful_payment
    payload = payment.invoice_payload  # e.g. "plan_week"
    plan_key = payload.replace("plan_", "")
    plan = STAR_PLANS.get(plan_key, {})
    days = plan.get("days", 7)
    
    if days > 0:
        now = _time.time()
        existing = paid_users.get(uid, {}).get("paid_until", now)
        start = max(existing, now)
        paid_users[uid] = {"paid_until": start + days * 86400, "plan": plan_key}
    
    session = get_session(uid)
    session["count"] = 0  # reset message counter
    
    stars = payment.total_amount
    user = message.from_user

    # ── Persist to platform-api (same as Cryptomus/TBC) ──
    try:
        import aiohttp
        async with aiohttp.ClientSession() as http:
            await http.post(
                f"{PLATFORM_API_URL}/internal/activate",
                json={
                    "user_id": uid,
                    "plan": plan_key,
                    "payment_method": "telegram_stars",
                    "payment_ref": f"stars_{payment.telegram_payment_charge_id}",
                    "stars": stars,
                    "username": user.username or "",
                    "full_name": user.full_name or "",
                },
                headers={"X-Internal-Key": PLATFORM_API_KEY},
                timeout=aiohttp.ClientTimeout(total=10),
            )
        logger.info(f"Stars payment synced to platform-api: uid={uid} plan={plan_key}")
    except Exception as e:
        logger.error(f"Failed to sync Stars payment to platform-api: {e}")
        # Payment still works locally even if platform-api is down

    # ── Computer Use activation ──
    if plan_key == "cu_activation":
        await activate_cu(message, uid, user, stars)
        return

    lang = session.get("lang", "ru")
    plan_name = plan.get("title", plan_key).split("—")[0].strip() if plan else plan_key

    # ── Step 1: Payment confirmation ──
    await message.answer(
        f"🎉 <b>Оплата прошла!</b> {stars} ⭐\n\n"
        f"✅ План <b>{plan_name}</b> активирован.\n"
        f"Давайте настроим вашего AI-ассистента! 👇"
    )

    # ── Step 2: Onboarding — ask about business ──
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
    
    # Notify admin
    try:
        await bot.send_message(ADMIN_ID,
            f"💰 <b>ОПЛАТА!</b>\n"
            f"👤 {user.full_name}{(' (@' + user.username + ')') if user.username else ''}\n"
            f"🆔 {user.id}\n"
            f"⭐ {stars} stars — план: {plan_key}\n"
            f"📝 Помощник: {session.get('persona', 'рецепционист')[:200]}")
    except: pass
    
    logger.info(f"Payment: {uid} paid {stars} stars for {plan_key}")


@dp.callback_query(F.data == "pay_bank")
async def on_pay_bank(callback: types.CallbackQuery):
    bank_text = (
        "💳 <b>Банковский перевод</b>\n\n"
        "Реквизиты для оплаты:\n\n"
        "🏦 <b>TBC Bank</b>\n"
        "IBAN: <code>GE51TB7866536010100033</code>\n"
        "Получатель: Timur Tokazov\n"
        "Валюта: GEL (конвертация по курсу банка)\n\n"
        "📌 В назначении укажите: AI Centers + ваш Telegram @username\n\n"
        "После перевода отправьте скриншот квитанции @CARGORAPIDO для активации."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📞 Написать менеджеру", url="https://t.me/CARGORAPIDO")],
        [InlineKeyboardButton(text="← Назад", callback_data="funnel_pricing")],
    ])
    await callback.message.answer(bank_text, reply_markup=kb)
    await callback.answer()

@dp.callback_query(F.data.startswith("pay_"))
async def on_pay_callback(callback: types.CallbackQuery):
    plan_key = callback.data.replace("pay_", "")
    # Handle cu_activation_stars → cu_activation
    if plan_key == "cu_activation_stars":
        plan_key = "cu_activation"
    if plan_key not in STAR_PLANS:
        await callback.answer("❌ Тариф не найден")
        return
    await send_stars_invoice(callback.message, plan_key)
    await callback.answer()


async def show_funnel_step1(message: types.Message):
    """Show sales funnel: 3 blocks on /start."""
    logger.info(f"FUNNEL_STEP1 called for user {message.from_user.id}")
    uid = message.from_user.id
    session = get_session(uid)
    lang = session.get("lang") or detect_lang(message.from_user)
    session["lang"] = lang
    session["funnel_shown"] = True
    name = message.from_user.first_name or "друг"

    # ── Block 1: Business qualification ──
    welcome_texts = {
        "ru": f"👋 {name}, привет!\n\nЯ помогу автоматизировать ваш бизнес за 5 минут.\n<b>Какой у вас бизнес?</b>",
        "en": f"👋 Hi {name}!\n\nI'll help automate your business in 5 minutes.\n<b>What's your business?</b>",
        "ka": f"👋 გამარჯობა, {name}!\n\nდაგეხმარებით ბიზნესის ავტომატიზაციაში 5 წუთში.\n<b>რა ბიზნესი გაქვთ?</b>",
        "tr": f"👋 Merhaba {name}!\n\nİşinizi 5 dakikada otomatikleştirmenize yardımcı olacağım.\n<b>İşiniz ne?</b>",
        "kk": f"👋 {name}, сәлем!\n\nБизнесіңізді 5 минутта автоматтандыруға көмектесемін.",
        "uz": f"👋 Salom, {name}!\n\nBiznesingizni 5 daqiqada avtomatlashtiraman.",
    }
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "biz_restaurant"), callback_data="biz_restaurant"),
         InlineKeyboardButton(text=t(lang, "biz_clinic"), callback_data="biz_clinic")],
        [InlineKeyboardButton(text=t(lang, "biz_salon"), callback_data="biz_salon"),
         InlineKeyboardButton(text=t(lang, "biz_shop"), callback_data="biz_shop")],
        [InlineKeyboardButton(text=t(lang, "biz_services"), callback_data="biz_services"),
         InlineKeyboardButton(text=t(lang, "biz_other"), callback_data="biz_other")],
        [InlineKeyboardButton(text="🖥 AI Computer Use", callback_data="biz_computer")],
        [InlineKeyboardButton(text=t(lang, "btn_order_assistant"), callback_data="funnel_pricing")],
    ])
    await message.answer(welcome_texts.get(lang, welcome_texts["en"]), reply_markup=kb)

    # ── Block 2: Demo CTA ──
    demo_texts = {
        "ru": "🎯 <b>Попробуйте демо-ассистента!</b>\n\nВыберите нишу и пообщайтесь как клиент.\nТакой же бот будет у вас — настроенный под ваш бизнес!",
        "en": "🎯 <b>Try the demo assistant!</b>\n\nChoose a niche and chat as a customer.\nThe same bot will be yours — customized for your business!",
        "ka": "🎯 <b>სცადეთ დემო ასისტენტი!</b>\n\nაირჩიეთ ნიშა და ესაუბრეთ როგორც კლიენტი.\nიგივე ბოტი იქნება თქვენი — მორგებული!",
        "tr": "🎯 <b>Demo asistanı deneyin!</b>\n\nBir niş seçin ve müşteri gibi sohbet edin.\nAynı bot sizin olacak — işletmenize özel!",
        "kk": "🎯 <b>Демо-ассистентті байқап көріңіз!</b>",
        "uz": "🎯 <b>Demo-assistentni sinab ko'ring!</b>",
    }
    demo_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_open_demo"), url="https://t.me/aicenters_demo_bot")],
    ])
    await message.answer(demo_texts.get(lang, demo_texts["en"]), reply_markup=demo_kb)

    # ── Block 3: Computer Use ──
    cu_texts = {
        "ru": "🖥 <b>AI Computer Use — работает в ваших программах</b>\n\nAI сам открывает, заполняет, обрабатывает в AmoCRM, 1С, Bitrix24.",
        "en": "🖥 <b>AI Computer Use — works in your software</b>\n\nAI opens, fills, processes in AmoCRM, 1C, Bitrix24 by itself.",
        "ka": "🖥 <b>AI Computer Use — მუშაობს თქვენს პროგრამებში</b>\n\nAI თავად ხსნის, ავსებს, ამუშავებს AmoCRM, 1C, Bitrix24-ში.",
        "tr": "🖥 <b>AI Computer Use — programlarınızda çalışır</b>\n\nAI, AmoCRM, 1C, Bitrix24'te açar, doldurur, işler.",
        "kk": "🖥 <b>AI Computer Use — бағдарламаларыңызда жұмыс істейді</b>",
        "uz": "🖥 <b>AI Computer Use — dasturlaringizda ishlaydi</b>",
    }
    cu_pilot_btn = {"ru": "🚀 Запустить пилот", "en": "🚀 Start Pilot", "ka": "🚀 პილოტის გაშვება", "tr": "🚀 Pilotu Başlat", "kk": "🚀 Пилотты іске қосу", "uz": "🚀 Pilotni ishga tushirish"}
    cu_pricing_btn = {"ru": "📋 Тарифы", "en": "📋 Pricing", "ka": "📋 ტარიფები", "tr": "📋 Tarifeler", "kk": "📋 Тарифтер", "uz": "📋 Tariflar"}
    cu_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=cu_pilot_btn.get(lang, cu_pilot_btn["en"]), callback_data="cu_funnel_pilot"),
         InlineKeyboardButton(text=cu_pricing_btn.get(lang, cu_pricing_btn["en"]), callback_data="cu_funnel_pricing")],
    ])
    await message.answer(cu_texts.get(lang, cu_texts["en"]), reply_markup=cu_kb)
    logger.info(f"Funnel step 1 (3 blocks): {uid} lang={lang}")


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    logger.info(f"CMD_START called for user {message.from_user.id}, payload: {message.text}")
    uid = message.from_user.id
    lang = detect_lang(message.from_user)
    sessions[uid] = {"history": [], "count": 0, "mode": "receptionist", "persona": None, "lang": lang, "funnel_shown": False, "funnel_step": None}
    
    # Handle deep links: /start partner, /start buy_starter, etc.
    args = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
    
    if args == "partner":
        # Partner program registration
        partner_text = (
            "🤝 <b>Партнёрская программа AI Centers</b>\n\n"
            "Зарабатывайте <b>от 20% до 50%</b> с каждого клиента!\n\n"
            "📈 <b>Как это работает:</b>\n"
            "1. Вы рекомендуете AI Centers бизнесам\n"
            "2. Мы создаём и настраиваем AI-бота\n"
            "3. Вы получаете комиссию каждый месяц\n\n"
            "💰 <b>Уровни комиссии:</b>\n"
            "• 1-5 клиентов → <b>20%</b>\n"
            "• 6-20 клиентов → <b>35%</b>\n"
            "• 21+ клиентов → <b>50%</b>\n\n"
            "0 вложений. 0 рисков. Рекуррентный доход.\n\n"
            "Напишите ваше имя и город, чтобы зарегистрироваться как партнёр 👇"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Подробнее на сайте", url="https://aicenters.co/partners")],
            [InlineKeyboardButton(text="📞 Связаться с менеджером", url="https://t.me/CARGORAPIDO")],
            [InlineKeyboardButton(text="← Назад в меню", callback_data="back_menu")],
        ])
        await message.answer(partner_text, reply_markup=kb)
        sessions[uid]["mode"] = "partner_registration"
        # Notify admin
        try:
            await bot.send_message(ADMIN_ID, f"🤝 Новый партнёр!\n@{message.from_user.username or '?'} ({message.from_user.full_name})\nID: {uid}")
        except Exception:
            pass
        logger.info(f"Partner signup: {uid} ({message.from_user.full_name})")
        return
    
    if args.startswith("buy_"):
        plan = args.replace("buy_", "")
        plan_names = {"starter": "Starter ($15/мес)", "pro": "Pro ($29/мес)", "business": "Business ($59/мес)", "enterprise": "Enterprise ($149/мес)"}
        plan_stars = {"starter": 250, "pro": 500, "business": 1000, "enterprise": 2500}
        if plan in plan_names:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f"⭐ Оплатить {plan_stars[plan]} Stars", callback_data=f"pay_{plan}")],
                [InlineKeyboardButton(text="💳 Банковский перевод", callback_data="pay_bank")],
            ])
            await message.answer(
                f"🤖 <b>Тариф {plan_names[plan]}</b>\n\n"
                f"Выберите способ оплаты:",
                reply_markup=kb
            )
            logger.info(f"Buy {plan}: {uid}")
            return

    if args == "computer_use_pilot":
        session = get_session(uid)
        session["mode"] = "cu_pilot"
        session["cu_pilot_step"] = 1
        session["cu_pilot_data"] = {}
        session["funnel_shown"] = True
        pilot_texts = {
            "ru": ("🚀 <b>Пилот AI Computer Use</b>\n\n"
                   "Отлично! Запускаем пилот.\n"
                   "Ответьте на 3 вопроса:\n\n"
                   "<b>1/3. Какую систему используете?</b>"),
            "en": ("🚀 <b>Free AI Computer Use Pilot</b>\n\n"
                   "Great! Let's start the pilot.\n"
                   "Answer 3 questions:\n\n"
                   "<b>1/3. What system do you use?</b>"),
        }
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="AmoCRM", callback_data="cu_sys_amocrm"),
             InlineKeyboardButton(text="Bitrix24", callback_data="cu_sys_bitrix")],
            [InlineKeyboardButton(text="1C", callback_data="cu_sys_1c"),
             InlineKeyboardButton(text="Google Sheets", callback_data="cu_sys_gsheets")],
            [InlineKeyboardButton(text="Другое / Other", callback_data="cu_sys_other")],
        ])
        await message.answer(pilot_texts.get(lang, pilot_texts["en"]), reply_markup=kb)
        logger.info(f"CU Pilot start: {uid}")
        return

    if args == "computer_use_demo":
        session = get_session(uid)
        session["mode"] = "cu_demo"
        session["funnel_shown"] = True
        demo_texts = {
            "ru": ("📅 <b>Демо AI Computer Use</b>\n\n"
                   "Запланируем демо в вашей системе за 30 минут.\n\n"
                   "<b>Когда вам удобно?</b>\n"
                   "Напишите день и время 👇"),
            "en": ("📅 <b>AI Computer Use Demo</b>\n\n"
                   "Let's schedule a 30-minute demo in your system.\n\n"
                   "<b>When works for you?</b>\n"
                   "Write a day and time 👇"),
        }
        await message.answer(demo_texts.get(lang, demo_texts["en"]))
        logger.info(f"CU Demo start: {uid}")
        return

    if args == "computer_use_start":
        session = get_session(uid)
        session["funnel_shown"] = True
        start_texts = {
            "ru": ("🖥 <b>AI Computer Use</b>\n\n"
                   "Отлично! Менеджер свяжется с вами и настроит AI-сотрудника под ваши задачи.\n\n"
                   "📞 Напишите ваш контакт (телефон или Telegram) 👇"),
            "en": ("🖥 <b>AI Computer Use</b>\n\n"
                   "Great! Our manager will contact you to set up the AI worker for your tasks.\n\n"
                   "📞 Write your contact (phone or Telegram) 👇"),
            "ka": ("🖥 <b>AI Computer Use</b>\n\n"
                   "შესანიშნავი! მენეჯერი დაგიკავშირდებათ და დააყენებს AI-თანამშრომელს.\n\n"
                   "📞 დაწერეთ თქვენი საკონტაქტო 👇"),
            "tr": ("🖥 <b>AI Computer Use</b>\n\n"
                   "Harika! Yöneticimiz sizinle iletişime geçip AI çalışanını kuracak.\n\n"
                   "📞 İletişim bilgilerinizi yazın 👇"),
        }
        session["mode"] = "cu_start_contact"
        await message.answer(start_texts.get(lang, start_texts["en"]))
        logger.info(f"CU Start: {uid}")
        return

    # ── Sales funnel: Step 1 ──
    await show_funnel_step1(message)


# ─── Sales Funnel Callbacks ───

# Niche names and cases are now in i18n.py


# Step 2a — Computer Use niche (separate flow)
@dp.callback_query(F.data == "biz_computer")
async def on_biz_computer(callback: types.CallbackQuery):
    uid = callback.from_user.id
    session = get_session(uid)
    lang = session.get("lang", detect_lang(callback.from_user))
    session["niche"] = "biz_computer"
    session["funnel_shown"] = True

    case_texts = {
        "ru": (
            "🖥 <b>AI Computer Use — работает в ваших программах</b>\n\n"
            "📦 <b>Кейс: логистическая компания</b>\n"
            "• AI сам вносит данные в 1С — 0 ошибок\n"
            "• Обрабатывает 500 накладных/день вместо 3 менеджеров\n"
            "• Экономия: <b>$2,400/мес</b> на зарплатах\n\n"
            "💰 Аддон от <b>$39/мес</b>. Настройка $299 (разово).\n"
            "Первые 3 дня — <b>пилот</b> в вашей системе."
        ),
        "en": (
            "🖥 <b>AI Computer Use — works in your software</b>\n\n"
            "📦 <b>Case: logistics company</b>\n"
            "• AI enters data into 1C — 0 errors\n"
            "• Processes 500 invoices/day instead of 3 managers\n"
            "• Savings: <b>$2,400/mo</b> on salaries\n\n"
            "💰 Add-on from <b>$39/mo</b>. Setup $299 (one-time).\n"
            "First 3 days — <b>pilot</b> in your system."
        ),
        "ka": (
            "🖥 <b>AI Computer Use — მუშაობს თქვენს პროგრამებში</b>\n\n"
            "📦 <b>ქეისი: ლოჯისტიკური კომპანია</b>\n"
            "• AI თავად შეაქვს მონაცემებს 1C-ში — 0 შეცდომა\n"
            "• ამუშავებს 500 ზედნადებს/დღეში 3 მენეჯერის ნაცვლად\n"
            "• დაზოგვა: <b>$2,400/თვე</b>\n\n"
            "💰 დანამატი <b>$39/თვე</b>-დან. დაყენება $299 (ერთჯერადი).\n"
            "პირველი 3 დღე — <b>პილოტი</b> თქვენს სისტემაში."
        ),
        "tr": (
            "🖥 <b>AI Computer Use — programlarınızda çalışır</b>\n\n"
            "📦 <b>Vaka: lojistik şirketi</b>\n"
            "• AI verileri 1C'ye girer — 0 hata\n"
            "• 3 yönetici yerine günde 500 irsaliye işler\n"
            "• Tasarruf: <b>$2,400/ay</b> maaşlardan\n\n"
            "💰 Eklenti <b>$39/ay</b>'dan. Kurulum $299 (tek seferlik).\n"
            "İlk 3 gün — sisteminizde <b>ücretsiz pilot</b>."
        ),
    }

    cu_pilot_btn = {"ru": "🚀 Запустить пилот", "en": "🚀 Start Pilot", "ka": "🚀 პილოტის გაშვება", "tr": "🚀 Pilotu Başlat"}
    cu_pricing_btn = {"ru": "💰 Тарифы", "en": "💰 Pricing", "ka": "💰 ტარიფები", "tr": "💰 Tarifeler"}
    cu_question_btn = {"ru": "❓ Задать вопрос", "en": "❓ Ask a Question", "ka": "❓ კითხვა", "tr": "❓ Soru Sorun"}

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=cu_pilot_btn.get(lang, cu_pilot_btn["en"]), callback_data="cu_funnel_pilot")],
        [InlineKeyboardButton(text=cu_pricing_btn.get(lang, cu_pricing_btn["en"]), callback_data="cu_funnel_pricing")],
        [InlineKeyboardButton(text=cu_question_btn.get(lang, cu_question_btn["en"]), callback_data="cu_funnel_question")],
    ])

    await callback.message.edit_text(case_texts.get(lang, case_texts["en"]), reply_markup=kb)
    await callback.answer()
    logger.info(f"CU funnel case shown: {uid} lang={lang}")


@dp.callback_query(F.data == "cu_funnel_pilot")
async def on_cu_funnel_pilot(callback: types.CallbackQuery):
    uid = callback.from_user.id
    session = get_session(uid)
    lang = session.get("lang", "ru")
    session["funnel_shown"] = True

    # Show explanation first
    explain = {
        "ru": (
            "🖥 <b>Как работает AI Computer Use?</b>\n\n"
            "AI-сотрудник работает прямо в вашем компьютере — как живой человек:\n"
            "• Открывает программы (AmoCRM, 1С, Bitrix24)\n"
            "• Заполняет формы, переносит данные\n"
            "• Отправляет письма и сообщения\n"
            "• Работает 24/7 без перерывов\n\n"
            "<b>Что нужно с вашей стороны:</b>\n"
            "💻 Компьютер включён и подключён к интернету\n"
            "🌐 Доступ к вашей системе (логин + пароль)\n"
            "📋 Список задач которые нужно автоматизировать\n\n"
            "Больше ничего — мы всё настроим сами.\n\n"
            "<b>Готовы запустить?</b>"
        ),
        "en": (
            "🖥 <b>How does AI Computer Use work?</b>\n\n"
            "An AI employee works directly on your computer — like a real person:\n"
            "• Opens programs (AmoCRM, 1C, Bitrix24)\n"
            "• Fills forms, transfers data\n"
            "• Sends emails and messages\n"
            "• Works 24/7 without breaks\n\n"
            "<b>What you need:</b>\n"
            "💻 Computer turned on and connected to internet\n"
            "🌐 Access to your system (login + password)\n"
            "📋 List of tasks to automate\n\n"
            "That's it — we'll set up everything.\n\n"
            "<b>Ready to start?</b>"
        ),
        "ka": (
            "🖥 <b>როგორ მუშაობს AI Computer Use?</b>\n\n"
            "AI-თანამშრომელი მუშაობს პირდაპირ თქვენს კომპიუტერში:\n"
            "• ხსნის პროგრამებს (AmoCRM, 1C, Bitrix24)\n"
            "• ავსებს ფორმებს, გადააქვს მონაცემები\n"
            "• აგზავნის წერილებს და შეტყობინებებს\n"
            "• მუშაობს 24/7\n\n"
            "<b>რა გჭირდებათ:</b>\n"
            "💻 ჩართული კომპიუტერი ინტერნეტით\n"
            "🌐 სისტემაში წვდომა\n"
            "📋 ავტომატიზაციის ამოცანების სია\n\n"
            "<b>მზად ხართ?</b>"
        ),
        "tr": (
            "🖥 <b>AI Computer Use nasıl çalışır?</b>\n\n"
            "AI çalışan doğrudan bilgisayarınızda çalışır — gerçek bir kişi gibi:\n"
            "• Programları açar (AmoCRM, 1C, Bitrix24)\n"
            "• Formları doldurur, verileri aktarır\n"
            "• E-posta ve mesaj gönderir\n"
            "• 7/24 mola vermeden çalışır\n\n"
            "<b>Sizden ne gerekiyor:</b>\n"
            "💻 Açık ve internete bağlı bilgisayar\n"
            "🌐 Sisteminize erişim (kullanıcı adı + şifre)\n"
            "📋 Otomatikleştirilecek görev listesi\n\n"
            "<b>Başlamaya hazır mısınız?</b>"
        ),
    }

    yes_btn = {"ru": "✅ Да, запустить", "en": "✅ Yes, start", "ka": "✅ დიახ, გაშვება", "tr": "✅ Evet, başlat"}
    q_btn = {"ru": "❓ Ещё вопросы", "en": "❓ More questions", "ka": "❓ კითხვები", "tr": "❓ Daha fazla soru"}

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=yes_btn.get(lang, yes_btn["en"]), callback_data="cu_start_questionnaire")],
        [InlineKeyboardButton(text=q_btn.get(lang, q_btn["en"]), callback_data="cu_funnel_question")],
    ])
    await callback.message.answer(explain.get(lang, explain["en"]), reply_markup=kb)
    await callback.answer()


@dp.callback_query(F.data == "cu_start_questionnaire")
async def on_cu_start_questionnaire(callback: types.CallbackQuery):
    uid = callback.from_user.id
    session = get_session(uid)
    lang = session.get("lang", "ru")
    session["mode"] = "cu_pilot"
    session["cu_pilot_step"] = 1
    session["cu_pilot_data"] = {}

    q1 = {
        "ru": "🚀 <b>Отлично! Запускаем.</b>\n\n<b>1/3. Какую систему используете?</b>",
        "en": "🚀 <b>Great! Let's go.</b>\n\n<b>1/3. What system do you use?</b>",
        "ka": "🚀 <b>შესანიშნავი! დავიწყოთ.</b>\n\n<b>1/3. რომელ სისტემას იყენებთ?</b>",
        "tr": "🚀 <b>Harika! Başlıyoruz.</b>\n\n<b>1/3. Hangi sistemi kullanıyorsunuz?</b>",
    }
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="AmoCRM", callback_data="cu_sys_amocrm"),
         InlineKeyboardButton(text="Bitrix24", callback_data="cu_sys_bitrix")],
        [InlineKeyboardButton(text="1C", callback_data="cu_sys_1c"),
         InlineKeyboardButton(text="Google Sheets", callback_data="cu_sys_gsheets")],
        [InlineKeyboardButton(text="Другое / Other", callback_data="cu_sys_other")],
    ])
    await callback.message.answer(q1.get(lang, q1["en"]), reply_markup=kb)
    await callback.answer()
    # Notify admin
    try:
        await bot.send_message(ADMIN_ID,
            f"🚀 <b>Пилот CU (из воронки)!</b>\n"
            f"👤 {callback.from_user.full_name} (@{callback.from_user.username or '?'})")
    except Exception:
        pass


@dp.callback_query(F.data == "cu_funnel_pricing")
async def on_cu_funnel_pricing(callback: types.CallbackQuery):
    uid = callback.from_user.id
    session = get_session(uid)
    lang = session.get("lang", "ru")

    pricing_texts = {
        "ru": (
            "💰 <b>Тарифы AI Computer Use</b>\n\n"
            "🟢 <b>Start — $39/мес</b>\n500 операций · 1 процесс\n\n"
            "🔵 <b>Growth — $99/мес</b> 🔥\n2,000 операций · 3 процесса\n\n"
            "🟣 <b>Scale — $299/мес</b>\n10,000 операций · 10 процессов\n\n"
            "⚡ <b>Unlimited — $599/мес</b>\n∞ операций · ∞ процессов\n\n"
            "➕ Настройка процесса: от $299 (разово)"
        ),
        "en": (
            "💰 <b>AI Computer Use Pricing</b>\n\n"
            "🟢 <b>Start — $39/mo</b>\n500 ops · 1 process\n\n"
            "🔵 <b>Growth — $99/mo</b> 🔥\n2,000 ops · 3 processes\n\n"
            "🟣 <b>Scale — $299/mo</b>\n10,000 ops · 10 processes\n\n"
            "⚡ <b>Unlimited — $599/mo</b>\n∞ ops · ∞ processes\n\n"
            "➕ Process setup: from $299 (one-time)"
        ),
        "ka": (
            "💰 <b>AI Computer Use ტარიფები</b>\n\n"
            "🟢 <b>Start — $39/თვე</b>\n500 ოპერაცია · 1 პროცესი\n\n"
            "🔵 <b>Growth — $99/თვე</b> 🔥\n2,000 ოპერაცია · 3 პროცესი\n\n"
            "🟣 <b>Scale — $299/თვე</b>\n10,000 ოპერაცია · 10 პროცესი\n\n"
            "⚡ <b>Unlimited — $599/თვე</b>\n∞ ოპერაცია · ∞ პროცესი"
        ),
        "tr": (
            "💰 <b>AI Computer Use Tarifeler</b>\n\n"
            "🟢 <b>Start — $39/ay</b>\n500 işlem · 1 süreç\n\n"
            "🔵 <b>Growth — $99/ay</b> 🔥\n2,000 işlem · 3 süreç\n\n"
            "🟣 <b>Scale — $299/ay</b>\n10,000 işlem · 10 süreç\n\n"
            "⚡ <b>Unlimited — $599/ay</b>\n∞ işlem · ∞ süreç"
        ),
    }

    start_btn = {"ru": "🚀 Запустить пилот", "en": "🚀 Start Pilot", "ka": "🚀 პილოტის გაშვება", "tr": "🚀 Pilotu Başlat"}
    back_btn = {"ru": "← Назад", "en": "← Back", "ka": "← უკან", "tr": "← Geri"}

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=start_btn.get(lang, start_btn["en"]), callback_data="cu_funnel_pilot")],
        [InlineKeyboardButton(text=back_btn.get(lang, back_btn["en"]), callback_data="back_menu")],
    ])
    await callback.message.answer(pricing_texts.get(lang, pricing_texts["en"]), reply_markup=kb)
    await callback.answer()


@dp.callback_query(F.data == "cu_funnel_question")
async def on_cu_funnel_question(callback: types.CallbackQuery):
    uid = callback.from_user.id
    session = get_session(uid)
    lang = session.get("lang", "ru")
    session["mode"] = "receptionist"
    session["funnel_shown"] = True

    q_texts = {
        "ru": "❓ Задайте вопрос про AI Computer Use — отвечу!",
        "en": "❓ Ask any question about AI Computer Use — I'll answer!",
        "ka": "❓ დასვით კითხვა AI Computer Use-ის შესახებ!",
        "tr": "❓ AI Computer Use hakkında sorunuzu sorun!",
    }
    await callback.message.answer(q_texts.get(lang, q_texts["en"]))
    await callback.answer()


# ── CU Pilot Stars payment button ──
@dp.callback_query(F.data == "pay_cu_activation_stars")
async def on_pay_cu_activation_stars(callback: types.CallbackQuery):
    await send_stars_invoice(callback.message, "cu_activation")
    await callback.answer()


# ── CU Activation (called after Stars payment) ──
async def activate_cu(message: types.Message, uid: int, user, stars: int):
    """Activate Computer Use: allow user + notify + onboard."""
    session = get_session(uid)
    lang = session.get("lang", "ru")
    data = session.get("cu_pilot_data", {})

    # 1. POST to computer-use-agent /users/allow
    cu_api = os.getenv("COMPUTER_USE_API_URL", "")
    if cu_api:
        try:
            import aiohttp
            async with aiohttp.ClientSession() as http:
                await http.post(
                    f"{cu_api}/users/allow",
                    json={"user_id": uid},
                    headers={"X-Internal-Key": PLATFORM_API_KEY},
                    timeout=aiohttp.ClientTimeout(total=10),
                )
            logger.info(f"CU Activation: user {uid} allowed on computer-use-agent")
        except Exception as e:
            logger.error(f"CU Activation: failed to allow user {uid}: {e}")

    # 2. Send activation message to client
    done = {
        "ru": (
            "🚀 <b>Система активирована!</b>\n\n"
            "Первый месяц — наш подарок 🎁\n\n"
            "Напишите боту — он уже готов работать:\n"
            "👉 @aicenters_computer_bot\n\n"
            "Опишите задачу (например: «Перенеси данные из Excel в 1С»), и AI выполнит!"
        ),
        "en": (
            "🚀 <b>System activated!</b>\n\n"
            "First month is our gift 🎁\n\n"
            "Write to the bot — it's ready to work:\n"
            "👉 @aicenters_computer_bot\n\n"
            "Describe a task (e.g.: 'Transfer data from Excel to 1C') and AI will do it!"
        ),
        "ka": (
            "🚀 <b>სისტემა გააქტიურებულია!</b>\n\n"
            "პირველი თვე — ჩვენი საჩუქარი 🎁\n\n"
            "მიწერეთ ბოტს:\n👉 @aicenters_computer_bot"
        ),
        "tr": (
            "🚀 <b>Sistem aktif!</b>\n\n"
            "İlk ay — bizden hediye 🎁\n\n"
            "Bota yazın:\n👉 @aicenters_computer_bot"
        ),
    }
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Открыть Computer Bot", url="https://t.me/aicenters_computer_bot")],
        [InlineKeyboardButton(text="← Меню", callback_data="back_menu")],
    ])
    await message.answer(done.get(lang, done["en"]), reply_markup=kb)

    # 3. Notify admin
    try:
        await bot.send_message(ADMIN_ID,
            f"💰🖥 <b>ОПЛАТА Computer Use — Активация!</b>\n\n"
            f"👤 {user.full_name} (@{getattr(user, 'username', '?') or '?'})\n"
            f"🆔 {uid}\n"
            f"⭐ {stars} Stars\n"
            f"🖥 Система: {data.get('system', '?')}\n"
            f"⚙️ Процесс: {data.get('process', '?')}\n"
            f"📞 Контакт: {data.get('contact', '?')}")
    except Exception:
        pass

    session["mode"] = "receptionist"
    session["cu_pilot_step"] = None
    logger.info(f"CU Activated: {uid} stars={stars}")


# Back to Step 1 — niche selection
@dp.callback_query(F.data == "back_step1")
async def on_back_step1(callback: types.CallbackQuery):
    uid = callback.from_user.id
    session = get_session(uid)
    lang = session.get("lang", detect_lang(callback.from_user))
    name = callback.from_user.first_name or "👋"
    welcome_texts = {
        "ru": f"👋 {name}, привет!\n\nЯ помогу автоматизировать ваш бизнес за 5 минут.\n<b>Какой у вас бизнес?</b>",
        "en": f"👋 Hi, {name}!\n\nI'll help automate your business in 5 minutes.\n<b>What's your business?</b>",
        "ka": f"👋 გამარჯობა, {name}!\n\n5 წუთში თქვენს ბიზნესს ავტომატიზირებთ.\n<b>რა ბიზნესი გაქვთ?</b>",
        "tr": f"👋 Merhaba, {name}!\n\nİşinizi 5 dakikada otomatikleştireceğim.\n<b>İşiniz nedir?</b>",
    }
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "biz_restaurant"), callback_data="biz_restaurant"),
         InlineKeyboardButton(text=t(lang, "biz_clinic"), callback_data="biz_clinic")],
        [InlineKeyboardButton(text=t(lang, "biz_salon"), callback_data="biz_salon"),
         InlineKeyboardButton(text=t(lang, "biz_shop"), callback_data="biz_shop")],
        [InlineKeyboardButton(text=t(lang, "biz_services"), callback_data="biz_services"),
         InlineKeyboardButton(text=t(lang, "biz_other"), callback_data="biz_other")],
        [InlineKeyboardButton(text="🖥 AI Computer Use", callback_data="biz_computer")],
        [InlineKeyboardButton(text=t(lang, "btn_order_assistant"), callback_data="funnel_pricing")],
    ])
    await callback.message.edit_text(welcome_texts.get(lang, welcome_texts["en"]), reply_markup=kb)
    await callback.answer()


# Step 2 — Pain point
@dp.callback_query(F.data.startswith("biz_"))
async def on_biz_select(callback: types.CallbackQuery):
    uid = callback.from_user.id
    session = get_session(uid)
    session["niche"] = callback.data
    lang = session.get("lang", detect_lang(callback.from_user))

    niche_name = t(lang, callback.data)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "leads_10"), callback_data="leads_10")],
        [InlineKeyboardButton(text=t(lang, "leads_50"), callback_data="leads_50")],
        [InlineKeyboardButton(text=t(lang, "leads_100"), callback_data="leads_100")],
        [InlineKeyboardButton(text=t(lang, "leads_unknown"), callback_data="leads_unknown")],
        [InlineKeyboardButton(text="← Назад", callback_data="back_step1")],
    ])

    await callback.message.edit_text(
        t(lang, "leads_question", niche=niche_name),
        reply_markup=kb,
    )
    await callback.answer()


# Step 3 — Case presentation
NICHE_TO_CASE = {
    "biz_restaurant": "case_restaurant", "biz_clinic": "case_clinic",
    "biz_salon": "case_salon", "biz_shop": "case_shop",
    "biz_services": "case_services", "biz_other": "case_other",
}

@dp.callback_query(F.data.startswith("leads_"))
async def on_leads_select(callback: types.CallbackQuery):
    uid = callback.from_user.id
    session = get_session(uid)
    niche = session.get("niche", "biz_other")
    leads = callback.data
    lang = session.get("lang", detect_lang(callback.from_user))

    # Get savings in user language
    savings_dict = I18N.get("savings", {}).get(leads, I18N["savings"]["leads_unknown"])
    save_text = savings_dict.get(lang, savings_dict.get("en", savings_dict.get("ru", "")))

    case_key = NICHE_TO_CASE.get(niche, "case_other")
    case = t(lang, case_key)
    offer_text = t(lang, "offer", savings=save_text)

    # Case + offer in one message with buttons
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_order_assistant"), callback_data="funnel_pricing")],
        [InlineKeyboardButton(text=t(lang, "btn_try_free"), callback_data="funnel_demo")],
        [InlineKeyboardButton(text=t(lang, "btn_question"), callback_data="funnel_question")],
        [InlineKeyboardButton(text="← Назад", callback_data="back_step1")],
    ])

    await callback.message.edit_text(
        f"{case}\n\n{'─' * 30}\n\n{offer_text}",
        reply_markup=kb,
    )
    await callback.answer()


# Step 5a — Free trial → demo bot
@dp.callback_query(F.data == "funnel_demo")
async def on_funnel_demo(callback: types.CallbackQuery):
    uid = callback.from_user.id
    session = get_session(uid)
    lang = session.get("lang", detect_lang(callback.from_user))
    niche = session.get("niche", "biz_other")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_open_demo"), url="https://t.me/aicenters_demo_bot")],
        [InlineKeyboardButton(text=t(lang, "btn_create_site"), callback_data="create")],
        [InlineKeyboardButton(text=t(lang, "btn_go_pricing"), callback_data="funnel_pricing")],
    ])

    await callback.message.edit_text(
        t(lang, "demo_intro"),
        reply_markup=kb,
    )
    await callback.answer()

    try:
        niche_name = t(lang, niche)
        await bot.send_message(ADMIN_ID,
            f"🔥 Лид (демо)!\n{callback.from_user.full_name} (@{callback.from_user.username or '?'})\n"
            f"Ниша: {niche_name}\nLang: {lang}\nID: {uid}")
    except: pass


# Step 5b — Pricing (Starter as main option)
PRICING_DETAILS = {
    "ru": (
        "⭐ <b>Starter — $149 + $19/мес</b> ← 90% клиентов начинают здесь\n"
        "• 1 AI-сотрудник\n• Telegram + WhatsApp + сайт\n• Обучение на ваших данных\n• Настройка за 5 минут\n\n"
        "🚀 <b>Pro — $299 + $49/мес</b>\n• 3 AI-сотрудника\n• CRM интеграция\n• Приоритетная поддержка\n\n"
        "🏢 <b>Business — $499 + $79/мес</b>\n• 10 AI-сотрудников\n• API + webhook\n• Персональный менеджер"
    ),
    "en": (
        "⭐ <b>Starter — $149 + $19/mo</b> ← 90% of clients start here\n"
        "• 1 AI employee\n• Telegram + WhatsApp + website\n• Trained on your data\n• Setup in 5 minutes\n\n"
        "🚀 <b>Pro — $299 + $49/mo</b>\n• 3 AI employees\n• CRM integration\n• Priority support\n\n"
        "🏢 <b>Business — $499 + $79/mo</b>\n• 10 AI employees\n• API + webhook\n• Personal manager"
    ),
    "ka": (
        "⭐ <b>Starter — $149 + $19/თვე</b> ← კლიენტების 90% აქედან იწყებს\n"
        "• 1 AI თანამშრომელი\n• Telegram + WhatsApp + საიტი\n• თქვენს მონაცემებზე სწავლება\n• დაყენება 5 წუთში\n\n"
        "🚀 <b>Pro — $299 + $49/თვე</b>\n• 3 AI თანამშრომელი\n• CRM ინტეგრაცია\n• პრიორიტეტული მხარდაჭერა\n\n"
        "🏢 <b>Business — $499 + $79/თვე</b>\n• 10 AI თანამშრომელი\n• API + webhook\n• პერსონალური მენეჯერი"
    ),
    "tr": (
        "⭐ <b>Starter — $149 + $19/ay</b> ← Müşterilerin %90'ı buradan başlıyor\n"
        "• 1 AI çalışan\n• Telegram + WhatsApp + web sitesi\n• Verilerinizle eğitim\n• 5 dakikada kurulum\n\n"
        "🚀 <b>Pro — $299 + $49/ay</b>\n• 3 AI çalışan\n• CRM entegrasyonu\n• Öncelikli destek\n\n"
        "🏢 <b>Business — $499 + $79/ay</b>\n• 10 AI çalışan\n• API + webhook\n• Kişisel yönetici"
    ),
    "kk": (
        "⭐ <b>Starter — $149 + $19/ай</b> ← 90% клиенттер осыдан бастайды\n"
        "• 1 AI қызметкер\n• Telegram + WhatsApp + сайт\n• Деректеріңізде оқыту\n• 5 минутта баптау\n\n"
        "🚀 <b>Pro — $299 + $49/ай</b>\n• 3 AI қызметкер\n• CRM интеграция\n\n"
        "🏢 <b>Business — $499 + $79/ай</b>\n• 10 AI қызметкер\n• API + webhook"
    ),
    "uz": (
        "⭐ <b>Starter — $149 + $19/oy</b> ← Mijozlarning 90% shu yerdan boshlaydi\n"
        "• 1 AI xodim\n• Telegram + WhatsApp + sayt\n• Ma'lumotlaringizda o'qitish\n• 5 daqiqada sozlash\n\n"
        "🚀 <b>Pro — $299 + $49/oy</b>\n• 3 AI xodim\n• CRM integratsiya\n\n"
        "🏢 <b>Business — $499 + $79/oy</b>\n• 10 AI xodim\n• API + webhook"
    ),
}

@dp.callback_query(F.data == "funnel_pricing")
async def on_funnel_pricing(callback: types.CallbackQuery):
    uid = callback.from_user.id
    session = get_session(uid)
    lang = session.get("lang", detect_lang(callback.from_user))

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "pricing_starter_label"), callback_data="funnel_buy_starter")],
        [InlineKeyboardButton(text="🚀 Pro — $299 + $49/mo", callback_data="funnel_buy_pro")],
        [InlineKeyboardButton(text="🏢 Business — $499 + $79/mo", callback_data="funnel_buy_business")],
        [InlineKeyboardButton(text=t(lang, "btn_try_free_short"), callback_data="funnel_demo")],
        [InlineKeyboardButton(text=t(lang, "btn_help_choose"), callback_data="funnel_question")],
    ])

    details = PRICING_DETAILS.get(lang, PRICING_DETAILS["en"])
    await callback.message.edit_text(
        f"{t(lang, 'pricing_title')}\n\n{details}\n\n{t(lang, 'pricing_footer')}",
        reply_markup=kb,
    )
    await callback.answer()


# Funnel buy → checkout
@dp.callback_query(F.data.startswith("funnel_buy_"))
async def on_funnel_buy(callback: types.CallbackQuery):
    uid = callback.from_user.id
    session = get_session(uid)
    lang = session.get("lang", detect_lang(callback.from_user))
    plan = callback.data.replace("funnel_buy_", "")
    plan_data = {
        "starter": {"name": "Starter", "setup": "$149", "monthly": "$19/mo", "stars": 250},
        "pro": {"name": "Pro", "setup": "$299", "monthly": "$49/mo", "stars": 500},
        "business": {"name": "Business", "setup": "$499", "monthly": "$79/mo", "stars": 1000},
    }
    p = plan_data.get(plan, plan_data["starter"])

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_pay_stars", stars=p["stars"]), callback_data=f"pay_{plan}")],
        [InlineKeyboardButton(text=t(lang, "btn_crypto"), url=f"https://aicenters.co/checkout?plan={plan}&lang={lang}")],
        [InlineKeyboardButton(text=t(lang, "btn_bank"), callback_data="pay_bank")],
        [InlineKeyboardButton(text=t(lang, "btn_back_pricing"), callback_data="funnel_pricing")],
    ])

    await callback.message.edit_text(
        t(lang, "payment_choose", plan=p["name"], setup=p["setup"], monthly=p["monthly"]),
        reply_markup=kb,
    )
    await callback.answer()

    try:
        await bot.send_message(ADMIN_ID,
            f"💰 Лид (оплата)!\n{callback.from_user.full_name} (@{callback.from_user.username or '?'})\n"
            f"План: {p['name']}\nLang: {lang}\nID: {uid}")
    except: pass


# Step 5c — Question → Gemini handles objections, then returns to offer
@dp.callback_query(F.data == "funnel_question")
async def on_funnel_question(callback: types.CallbackQuery):
    uid = callback.from_user.id
    session = get_session(uid)
    session["mode"] = "objection_handler"
    lang = session.get("lang", detect_lang(callback.from_user))

    await callback.message.edit_text(t(lang, "ask_question"))
    await callback.answer()


@dp.message(Command("reset"))
async def cmd_reset(message: types.Message):
    uid = message.from_user.id
    sessions[uid] = {"history": [], "count": 0, "mode": "receptionist", "persona": None}
    await message.answer("🔄 Начнём с чистого листа! Чем могу помочь?")


@dp.message(Command("test_pay"))
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


@dp.message(Command("menu"))
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


@dp.callback_query(F.data == "create")
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


@dp.callback_query(F.data == "computer_use")
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


@dp.callback_query(F.data == "computer_use_demo")
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

@dp.callback_query(F.data.startswith("cu_sys_"))
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

async def handle_cu_text(message: types.Message, session: dict) -> bool:
    """Handle CU pilot/demo text. Returns True if handled."""
    uid = message.from_user.id
    lang = session.get("lang", "ru")
    text = message.text or ""
    mode = session.get("mode")

    if mode == "cu_pilot" and session.get("cu_pilot_step") == 2:
        session.setdefault("cu_pilot_data", {})["process"] = text
        session["cu_pilot_step"] = 3
        q3 = {
            "ru": "<b>3/3. Ваш контакт для связи?</b>\n\nТелефон или Telegram 👇",
            "en": "<b>3/3. Your contact info?</b>\n\nPhone or Telegram 👇",
        }
        await message.answer(q3.get(lang, q3["en"]))
        return True

    if mode == "cu_pilot" and session.get("cu_pilot_step") == 3:
        session.setdefault("cu_pilot_data", {})["contact"] = text
        data = session["cu_pilot_data"]
        system = data.get("system", "CRM")
        # Notify admin about lead
        try:
            await bot.send_message(ADMIN_ID,
                f"🚀 <b>Лид Computer Use!</b>\n\n"
                f"👤 {message.from_user.full_name} (@{message.from_user.username or '?'})\n"
                f"🖥 Система: {data.get('system', '?')}\n"
                f"⚙️ Процесс: {data.get('process', '?')}\n"
                f"📞 Контакт: {data.get('contact', '?')}")
        except Exception:
            pass

        # Show activation offer with payment
        offer = {
            "ru": (
                "🎁 <b>Специальное предложение!</b>\n\n"
                f"Активация системы — <b>$249</b> (разово)\n"
                "✅ Первый месяц ($39) — <b>в подарок!</b>\n\n"
                "Что входит:\n"
                f"• Подключение AI к вашей системе ({system})\n"
                "• Настройка под ваш процесс\n"
                "• Первый месяц работы бесплатно\n\n"
                "Выберите способ оплаты:"
            ),
            "en": (
                "🎁 <b>Special offer!</b>\n\n"
                f"System activation — <b>$249</b> (one-time)\n"
                "✅ First month ($39) — <b>free!</b>\n\n"
                "Includes:\n"
                f"• AI connection to your system ({system})\n"
                "• Custom process setup\n"
                "• First month free\n\n"
                "Choose payment method:"
            ),
            "ka": (
                "🎁 <b>სპეციალური შეთავაზება!</b>\n\n"
                f"სისტემის აქტივაცია — <b>$249</b> (ერთჯერადი)\n"
                "✅ პირველი თვე ($39) — <b>საჩუქრად!</b>\n\n"
                f"• AI-ის დაკავშირება ({system})\n"
                "• პროცესის მორგება\n"
                "• პირველი თვე უფასო"
            ),
            "tr": (
                "🎁 <b>Özel teklif!</b>\n\n"
                f"Sistem aktivasyonu — <b>$249</b> (tek seferlik)\n"
                "✅ İlk ay ($39) — <b>hediye!</b>\n\n"
                f"• AI bağlantısı ({system})\n"
                "• Süreç kurulumu\n"
                "• İlk ay ücretsiz"
            ),
        }
        checkout_url = f"https://aicenters.co/checkout?plan=computer-use-activation&lang={lang}"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⭐ Telegram Stars — 19,154 ★", callback_data="pay_cu_activation_stars")],
            [InlineKeyboardButton(text="💎 Крипто (USDT/BTC)" if lang == "ru" else "💎 Crypto (USDT/BTC)", url=checkout_url)],
        ])
        await message.answer(offer.get(lang, offer["en"]), reply_markup=kb)
        session["cu_pilot_step"] = None
        session["mode"] = "receptionist"
        logger.info(f"CU activation offer: {uid} system={system}")
        return True

    if mode == "cu_demo":
        # Notify admin
        try:
            await bot.send_message(ADMIN_ID,
                f"📅 <b>Демо Computer Use!</b>\n\n"
                f"👤 {message.from_user.full_name} (@{message.from_user.username or '?'})\n"
                f"🕐 Время: {text}")
        except Exception:
            pass
        done = {
            "ru": "✅ <b>Подтверждаем демо!</b>\n\nОжидайте — мы свяжемся для подтверждения времени.",
            "en": "✅ <b>Demo confirmed!</b>\n\nWe'll contact you to confirm the time.",
        }
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="← Меню", callback_data="back_menu")],
        ])
        await message.answer(done.get(lang, done["en"]), reply_markup=kb)
        session["mode"] = "receptionist"
        logger.info(f"CU Demo scheduled: {uid} time={text}")
        return True

    if mode == "cu_start_contact":
        try:
            await bot.send_message(ADMIN_ID,
                f"🖥 <b>Новый клиент Computer Use (с сайта)!</b>\n\n"
                f"👤 {message.from_user.full_name} (@{message.from_user.username or '?'})\n"
                f"📞 Контакт: {text}")
        except Exception:
            pass
        done = {
            "ru": "✅ <b>Заявка принята!</b>\n\nМенеджер свяжется с вами в течение 2 часов.",
            "en": "✅ <b>Request received!</b>\n\nOur manager will contact you within 2 hours.",
            "ka": "✅ <b>მოთხოვნა მიღებულია!</b>\n\nმენეჯერი დაგიკავშირდებათ 2 საათში.",
            "tr": "✅ <b>Talep alındı!</b>\n\nYöneticimiz 2 saat içinde sizinle iletişime geçecek.",
        }
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="← Меню", callback_data="back_menu")],
        ])
        await message.answer(done.get(lang, done["en"]), reply_markup=kb)
        session["mode"] = "receptionist"
        logger.info(f"CU Start contact: {uid} contact={text}")
        return True

    return False


@dp.callback_query(F.data == "back_menu")
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


@dp.callback_query(F.data == "catalog")
async def on_catalog(callback: types.CallbackQuery):
    uid = callback.from_user.id
    session = get_session(uid)
    
    response = gemini_chat(SYSTEM_PROMPT, session["history"], "Покажи каталог готовых агентов. Какие есть?")
    session["history"].append({"user": "Покажи каталог", "bot": response})
    
    await callback.message.answer(response)
    await callback.answer()


@dp.callback_query(F.data == "voice_ai")
async def on_voice_ai(callback: types.CallbackQuery):
    uid = callback.from_user.id
    session = get_session(uid)
    
    response = gemini_chat(SYSTEM_PROMPT, session["history"],
        "[Система: клиент нажал кнопку 'Голосовой AI-секретарь'. Расскажи коротко что это: AI отвечает клиентам реалистичным голосом 24/7, от $300/мес. Спроси какой у него бизнес.]")
    session["history"].append({"user": "Расскажи про голосового AI-секретаря", "bot": response})
    
    await callback.message.answer(response)
    await callback.answer()


@dp.callback_query(F.data == "pricing")
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


@dp.message(F.voice)
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


@dp.message(F.text)
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
            session["ob_biz_name"] = text.strip()
            session["onboarding_step"] = 3
            await message.answer(
                f"✅ Компания: <b>{text.strip()}</b>\n\n"
                f"📋 <b>Шаг 3 из 4 — Задачи ассистента</b>\n\n"
                f"Что должен делать ваш AI-бот?\n"
                f"Например: <i>Отвечать на вопросы клиентов, принимать заказы, записывать на приём, рассказывать о ценах</i>",
            )
            return
        elif step == 3:
            # Step 3: got tasks → ask channel
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
                f"📋 <b>Шаг 4 из 4 — Где подключить?</b>\n\n"
                f"В каком канале будет работать ваш AI-ассистент?",
                reply_markup=ch_kb,
            )
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
                "6️⃣ Появится длинный код — это <b>токен</b>\n"
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
                        endpoint = f"{ENGINE_API_URL}/bots/auto-setup"
                    else:
                        payload = {
                            "bot_token": bot_token,
                            "name": biz_name,
                            "description": f"{niche}. {tasks}",
                            "tone": "дружелюбный, профессиональный",
                            "knowledge_base": f"Бизнес: {biz_name}\nНиша: {niche}\nЗадачи: {tasks}\n\n{knowledge}",
                        }
                        endpoint = f"{ENGINE_API_URL}/bots"

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
                    except: pass
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
                except: pass
            return
        else:
            await message.answer(
                "🤔 Это не похоже на токен бота.\n\n"
                "Токен выглядит так:\n<code>1234567890:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw</code>\n\n"
                "Скопируйте его из @BotFather и отправьте сюда.",
            )
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
        except: pass
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
            except: pass
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
            "Клиент интересуется AI-ботом для бизнеса, но задаёт вопросы перед покупкой. "
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
    if await handle_cu_text(message, session):
        return

    # === Funnel gate: always show funnel before Gemini ===
    if not session.get("funnel_shown"):
        return await show_funnel_step1(message)

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
            await send_stars_invoice(message, plan_key)
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
        except: pass
        
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
@dp.callback_query(F.data.startswith("ob_channel_"))
async def on_ob_channel(callback: types.CallbackQuery):
    uid = callback.from_user.id
    session = get_session(uid)
    channel = callback.data.replace("ob_channel_", "")
    session["ob_channel"] = channel
    session["onboarding_step"] = 5
    lang = session.get("lang", "ru")

    channel_names = {"telegram": "Telegram", "whatsapp": "WhatsApp", "website": "Сайт", "all": "Все каналы"}
    ch_name = channel_names.get(channel, channel)

    niche = session.get("ob_niche_name", "бизнес")
    biz_name = session.get("ob_biz_name", "Мой бизнес")
    tasks = session.get("ob_tasks", "общение с клиентами")

    summary = (
        f"🎉 <b>Настройка завершена!</b>\n\n"
        f"📊 <b>Ваш AI-ассистент:</b>\n"
        f"• Бизнес: {biz_name} ({niche})\n"
        f"• Задачи: {tasks[:200]}\n"
        f"• Канал: {ch_name}\n\n"
        f"⚡ <b>Создаём вашего ассистента...</b>\n\n"
        f"Отправьте материалы для обучения бота:\n"
        f"• 📎 Ссылка на сайт\n"
        f"• 📄 Прайс-лист, меню, FAQ\n"
        f"• 💬 Примеры переписок с клиентами\n\n"
        f"Чем больше данных — тем умнее бот.\n"
        f"Просто отправляйте файлы и ссылки прямо сюда 👇"
    )

    # Remove Step 4 buttons
    try:
        await callback.message.edit_text(f"✅ Канал: <b>{ch_name}</b>")
    except: pass
    await callback.answer()

    # Context-aware buttons based on niche
    niche_key = session.get("ob_niche", "other")
    buttons = [
        [InlineKeyboardButton(text="📎 Отправить ссылку на сайт", callback_data="ob_send_url")],
    ]
    # Niche-specific buttons
    if niche_key == "restaurant":
        buttons.append([InlineKeyboardButton(text="🍽 Загрузить меню ресторана", callback_data="ob_send_menu")])
    elif niche_key == "clinic":
        buttons.append([InlineKeyboardButton(text="🏥 Загрузить прайс услуг", callback_data="ob_send_price")])
    elif niche_key == "salon":
        buttons.append([InlineKeyboardButton(text="💇 Загрузить прайс услуг", callback_data="ob_send_price")])
    elif niche_key == "shop":
        buttons.append([InlineKeyboardButton(text="🛍 Загрузить каталог товаров", callback_data="ob_send_catalog")])
    else:
        buttons.append([InlineKeyboardButton(text="📄 Загрузить прайс / каталог", callback_data="ob_send_price")])

    buttons.append([InlineKeyboardButton(text="💬 Написать описание бизнеса", callback_data="ob_send_desc")])
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.answer(summary, reply_markup=kb)

    session["onboarding"] = False
    session["onboarding_step"] = 0
    session["awaiting_data"] = True

    # Notify admin (separate message, only admin sees it)
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
        except: pass


@dp.callback_query(F.data == "ob_more_data")
async def on_ob_more_data(callback: types.CallbackQuery):
    session = get_session(callback.from_user.id)
    session["awaiting_data"] = True
    await callback.message.answer(
        "📎 Отправляйте ещё материалы:\n"
        "• Ссылки, фото, PDF, текст\n"
        "• Всё пойдёт на обучение бота 👇"
    )
    await callback.answer()


@dp.callback_query(F.data == "ob_create_bot")
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
    except: pass


ENGINE_API_URL = os.getenv("ENGINE_API_URL", "https://ai-centers-dashboard-production.up.railway.app")

@dp.callback_query(F.data == "guide_telegram")
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


@dp.callback_query(F.data == "tg_standalone")
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


@dp.callback_query(F.data == "tg_business")
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


@dp.callback_query(F.data == "tg_group")
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


@dp.callback_query(F.data == "guide_whatsapp")
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


@dp.callback_query(F.data == "wa_meta")
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


@dp.callback_query(F.data == "meta_step1")
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


@dp.callback_query(F.data == "meta_step2")
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


@dp.callback_query(F.data == "meta_step3")
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


@dp.callback_query(F.data == "wa_wazzup")
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


@dp.callback_query(F.data == "wz_step1")
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


@dp.callback_query(F.data == "wz_step2")
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


@dp.callback_query(F.data == "wz_step3")
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


@dp.callback_query(F.data == "wz_step4")
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


@dp.callback_query(F.data == "wz_step5")
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


@dp.callback_query(F.data == "wa_app_only")
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


@dp.callback_query(F.data == "wa_twilio")
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


@dp.callback_query(F.data == "tw_step1")
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


@dp.callback_query(F.data == "tw_step2")
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


@dp.callback_query(F.data == "tw_step3")
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


@dp.callback_query(F.data == "tw_step4")
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


@dp.callback_query(F.data == "wa_meta_setup")
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


@dp.callback_query(F.data == "guide_website")
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


@dp.callback_query(F.data == "web_code")
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


@dp.callback_query(F.data == "web_wordpress")
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


@dp.callback_query(F.data == "web_tilda")
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


@dp.callback_query(F.data == "web_wix")
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


@dp.callback_query(F.data == "web_shopify")
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


@dp.callback_query(F.data == "web_link")
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


@dp.callback_query(F.data == "guide_instagram")
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


@dp.callback_query(F.data == "ig_meta")
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


@dp.callback_query(F.data == "ig_setup")
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


@dp.callback_query(F.data == "guide_back")
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

@dp.callback_query(F.data == "ob_manage_bot")
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


@dp.callback_query(F.data == "manage_train")
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


@dp.callback_query(F.data == "manage_edit")
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


@dp.callback_query(F.data == "manage_billing")
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


@dp.callback_query(F.data == "manage_faq")
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


@dp.callback_query(F.data == "ob_customize_bot")
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


@dp.callback_query(F.data == "ob_send_custom_request")
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


@dp.callback_query(F.data == "ob_bot_stats")
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


@dp.callback_query(F.data == "ob_help_botfather")
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


@dp.callback_query(F.data == "ob_send_url")
async def on_ob_send_url(callback: types.CallbackQuery):
    session = get_session(callback.from_user.id)
    session["awaiting_data"] = "url"
    await callback.message.answer(
        "🌐 <b>Отправьте ссылку на ваш сайт</b>\n\n"
        "Мы изучим сайт и обучим бота на его содержимом — меню, цены, услуги, FAQ.\n\n"
        "Просто отправьте URL 👇"
    )
    await callback.answer()


@dp.callback_query(F.data == "ob_send_menu")
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


@dp.callback_query(F.data.in_({"ob_send_price", "ob_send_catalog"}))
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


@dp.callback_query(F.data == "ob_send_desc")
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


@dp.callback_query(F.data.startswith("ob_"))
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


async def main():
    logger.info("AI Centers Receptionist (live mode) starting...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

