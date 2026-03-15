"""Shared state, config, and utilities for AI Centers Sales Bot."""

import os
import json
import logging
import time
import re
import collections
import urllib.request
import tempfile
import sqlite3

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from i18n import I18N

logger = logging.getLogger(__name__)

# ─── Config ──────────────────────────────────────────────────────────────────

TOKEN = os.getenv("BOT_TOKEN", "")
GEMINI_KEY = os.getenv("GEMINI_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
ADMIN_ID = 5309206282
FREE_LIMIT = 20

STARS_WEEK = 150
STARS_MONTH = 500
STARS_PREMIUM = 1500
STARS_CUSTOM = 3000
STARS_CU_ACTIVATION = 19154

# B2B Plans (Stars pricing: $1 ≈ 50 stars)
STARS_STARTER = 7450       # $149 setup
STARS_PRO = 14950          # $299 setup
STARS_BUSINESS = 24950     # $499 setup
STARS_ENTERPRISE = 74950   # $1499 setup

PLATFORM_API_URL = os.getenv("PLATFORM_API_URL", "https://platform-api-production-f313.up.railway.app")
PLATFORM_API_KEY = os.getenv("PLATFORM_API_KEY", "")
COMPUTER_USE_BOT = os.getenv("COMPUTER_USE_BOT", "aicenters_computer_bot")
ELEVENLABS_KEY = os.getenv("ELEVENLABS_KEY", "")
VOICE_ID = os.getenv("VOICE_ID", "EXAVITQu4vr4xnSDxMaL")
VOICE_ENABLED = bool(ELEVENLABS_KEY)
OPENAI_KEY = os.getenv("OPENAI_KEY", "")

SUPPORTED_LANGS = {"ru", "en", "ka", "tr", "kk", "uz"}

# ─── Bot & Dispatcher ────────────────────────────────────────────────────────

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())

# ─── Session store ────────────────────────────────────────────────────────────

sessions: dict[int, dict] = {}

# ─── SQLite Users DB ─────────────────────────────────────────────────────────

DB_PATH = os.getenv("DB_PATH", "/data/users.db")

def _init_db():
    """Initialize SQLite database for user tracking."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            uid INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            lang TEXT,
            first_seen TEXT DEFAULT (datetime('now')),
            last_seen TEXT DEFAULT (datetime('now')),
            paid INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def track_user(uid: int, username: str = None, full_name: str = None, lang: str = "ru"):
    """Register or update user in DB."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            INSERT INTO users (uid, username, full_name, lang)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(uid) DO UPDATE SET
                username = excluded.username,
                full_name = excluded.full_name,
                last_seen = datetime('now')
        """, (uid, username, full_name, lang))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"track_user error: {e}")

def mark_user_paid(uid: int):
    """Mark user as paid in DB."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("UPDATE users SET paid = 1 WHERE uid = ?", (uid,))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"mark_user_paid error: {e}")

def get_users_stats() -> dict:
    """Get user statistics."""
    try:
        conn = sqlite3.connect(DB_PATH)
        total = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        paid = conn.execute("SELECT COUNT(*) FROM users WHERE paid = 1").fetchone()[0]
        today = conn.execute("SELECT COUNT(*) FROM users WHERE date(first_seen) = date('now')").fetchone()[0]
        week = conn.execute("SELECT COUNT(*) FROM users WHERE first_seen >= datetime('now', '-7 days')").fetchone()[0]
        active_today = conn.execute("SELECT COUNT(*) FROM users WHERE date(last_seen) = date('now')").fetchone()[0]
        conn.close()
        return {"total": total, "paid": paid, "today": today, "week": week, "active_today": active_today}
    except Exception as e:
        logger.warning(f"get_users_stats error: {e}")
        return {"total": 0, "paid": 0, "today": 0, "week": 0, "active_today": 0}

# Initialize DB on import
try:
    _init_db()
except Exception as e:
    logger.warning(f"DB init error: {e}")

def get_session(uid: int) -> dict:
    """Get or create user session."""
    if uid not in sessions:
        sessions[uid] = {
            "history": [],
            "count": 0,
            "mode": "funnel",
            "step": None,
            "persona": "",
            "niche": "",
            "biz_name": "",
            "lang": "ru",
            "data": {},
        }
    return sessions[uid]

def is_paid(uid: int) -> bool:
    """Check if user has active paid plan."""
    s = get_session(uid)
    return s.get("paid", False) or s.get("plan") in ("week", "month", "premium", "custom")

# ─── i18n ─────────────────────────────────────────────────────────────────────

def detect_lang(user) -> str:
    """Detect language from Telegram language_code. Defaults to ru."""
    code = (user.language_code or "ru")[:2].lower()
    return code if code in SUPPORTED_LANGS else "ru"

def t(lang: str, key: str, **kwargs) -> str:
    """Get translated text. Falls back to en → ru."""
    texts = I18N.get(key, {})
    if isinstance(texts, str):
        return texts
    text = texts.get(lang, texts.get("en", texts.get("ru", key)))
    if kwargs:
        text = text.format(**kwargs)
    return text

# ─── Rate limiting ────────────────────────────────────────────────────────────

_rate_buckets: dict[int, collections.deque] = {}
RATE_LIMIT_PER_MINUTE = 30

def check_rate_limit(uid: int) -> bool:
    """Returns True if user exceeded rate limit."""
    now = time.time()
    if uid not in _rate_buckets:
        _rate_buckets[uid] = collections.deque()
    bucket = _rate_buckets[uid]
    while bucket and bucket[0] < now - 60:
        bucket.popleft()
    if len(bucket) >= RATE_LIMIT_PER_MINUTE:
        return True
    bucket.append(now)
    return False

# ─── Prompt injection detection ───────────────────────────────────────────────

_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous",
    r"forget\s+(all\s+)?instructions",
    r"you\s+are\s+now",
    r"system\s*prompt",
    r"new\s+instructions?",
    r"override\s+(all\s+)?rules",
    r"act\s+as\s+(?:a\s+)?(?:different|new)",
    r"reveal\s+(?:your\s+)?(?:system|instructions|prompt)",
    r"игнорируй\s+(?:все\s+)?(?:предыдущие|инструкции)",
    r"забудь\s+(?:все\s+)?(?:инструкции|правила)",
    r"ты\s+теперь",
    r"новые\s+инструкции",
    r"покажи\s+(?:свой\s+)?(?:системный|промпт)",
]
_INJECTION_RE = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE)

def detect_injection(text: str) -> bool:
    """Returns True if text looks like a prompt injection attempt."""
    return bool(_INJECTION_RE.search(text))

# ─── Gemini API ───────────────────────────────────────────────────────────────

def gemini_chat(system: str, history: list, user_msg: str) -> str:
    """Call Gemini API for chat completion."""
    if not GEMINI_KEY:
        return "AI временно недоступен."
    
    contents = []
    for msg in history[-10:]:
        contents.append({"role": msg["role"], "parts": [{"text": msg["text"]}]})
    contents.append({"role": "user", "parts": [{"text": user_msg}]})
    
    body = json.dumps({
        "system_instruction": {"parts": [{"text": system}]},
        "contents": contents,
        "generationConfig": {"maxOutputTokens": 1024, "temperature": 0.9}
    }).encode()
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_KEY}"
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return "Произошла ошибка. Попробуйте ещё раз."

# ─── Voice (ElevenLabs) ──────────────────────────────────────────────────────

async def text_to_voice(text: str) -> str | None:
    """Convert text to voice via ElevenLabs. Returns path to mp3 or None."""
    if not ELEVENLABS_KEY:
        return None
    try:
        body = json.dumps({
            "text": text[:1000],
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
        }).encode()
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
        req = urllib.request.Request(url, data=body, headers={
            "xi-api-key": ELEVENLABS_KEY,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            tmp.write(resp.read())
            tmp.close()
            return tmp.name
    except Exception as e:
        logger.error(f"ElevenLabs TTS error: {e}")
        return None

async def send_with_voice(message: types.Message, text: str, reply_markup=None):
    """Send text message + optional voice version."""
    await message.answer(text, reply_markup=reply_markup)
    if VOICE_ENABLED and len(text) > 50:
        voice_path = await text_to_voice(text)
        if voice_path:
            try:
                from aiogram.types import FSInputFile
                await message.answer_voice(FSInputFile(voice_path))
            except Exception as e:
                logger.warning(f"Voice send failed: {e}")
            finally:
                try:
                    import os as _os
                    _os.unlink(voice_path)
                except OSError:
                    pass

# ─── Admin notification helper ────────────────────────────────────────────────

async def notify_admin(text: str):
    """Send notification to admin. Silent fail."""
    try:
        await bot.send_message(ADMIN_ID, text)
    except Exception:
        pass

# ─── Engine API ───────────────────────────────────────────────────────────────

ENGINE_API_URL = os.getenv("ENGINE_API_URL", "https://platform-api-production-f313.up.railway.app")

# ─── Onboarding step helpers ─────────────────────────────────────────────────

def get_plan_total_steps(plan_key: str) -> int:
    """Get total onboarding steps based on plan features."""
    from handlers.payments import get_plan_features
    features = get_plan_features(plan_key)
    total = 4  # base: niche + name + tasks + channel
    if features.get("voice"):
        total += 1
    if features.get("crm"):
        total += 1
    return total

# ─── System Prompts ───────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Ты — AI-консультант компании AI Centers (aicenters.co).

Твоя задача: помочь бизнесу понять как AI может автоматизировать их работу и подвести к покупке.

Ты отвечаешь на вопросы про:
- AI-ассистентов для Telegram, WhatsApp, Instagram)
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
- Starter $149 + $19/мес — 1 AI-ассистент
- Pro $299 + $49/мес — 3 AI-ассистента
- Business $499 + $79/мес — 10 AI-ассистентов

Computer Use (ежемесячно):
- Start — $39/мес · 500 операций · 1 процесс
- Growth — $99/мес · 2,000 операций · 3 процесса
- Scale — $299/мес · 10,000 операций · 10 процессов
- Unlimited — $599/мес · безлимит
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
Отвечай конкретно и пошагово. Не перенаправляй на специалиста — ты и есть поддержка.

ЕСЛИ НЕ ЗНАЕШЬ ОТВЕТА — честно скажи и предложи написать подробнее.

ЕСЛИ КЛИЕНТ ЗАСТРЯЛ НА НАСТРОЙКЕ — предложи: "Скиньте скриншот — я подскажу куда нажать!" Это помогает быстро решить проблему.

⚠️ ЗАПРЕЩЕНО:
- НЕ рисуй кнопки текстом
- НЕ показывай меню и ссылки (@..._bot)
- НЕ рекомендуй сторонние сервисы
- НЕ говори "я всего лишь AI"

МАРКЕРЫ:
[CREATE_ASSISTANT: описание] — клиент описал бота
[PAY:week] [PAY:month] [PAY:premium] [PAY:custom] — готов платить

ЯЗЫК: отвечай на ТОМ ЖЕ языке клиента.
Сайт: aicenters.co | Основатель: @timurtokazov
"""

ASSISTANT_SYSTEM = """Ты — персональный AI-помощник. Твоя роль:
{persona}

ПРАВИЛА:
- Общайся живо, по-дружески, коротко
- Отвечай строго в рамках своей роли
- Используй HTML теги (<b>, <i>) умеренно
- ВСЕГДА отвечай на языке клиента
"""

