"""Payment handlers: Stars invoices, bank transfer, payment callbacks."""

import time
import logging
import aiohttp
from aiogram import Router, F, types
import aiohttp
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice

from core import (
    bot, ADMIN_ID, PLATFORM_API_URL, PLATFORM_API_KEY,
    STARS_WEEK, STARS_MONTH, STARS_PREMIUM, STARS_CUSTOM, STARS_CU_ACTIVATION,
    STARS_STARTER, STARS_PRO, STARS_BUSINESS, STARS_ENTERPRISE,
    get_session,
)

logger = logging.getLogger(__name__)
router = Router()

# === Stars Payment Handlers ===

STAR_PLANS = {
    "week": {"title": "AI Centers — Неделя ⭐", "description": "7 дней безлимитного общения с AI-помощником", "stars": STARS_WEEK, "days": 7},
    "month": {"title": "AI Centers — Месяц ⭐", "description": "30 дней безлимитного общения + все агенты", "stars": STARS_MONTH, "days": 30},
    "premium": {"title": "AI Centers Premium ⭐", "description": "30 дней — все агенты, приоритет, голосовые ответы", "stars": STARS_PREMIUM, "days": 30},
    "custom": {"title": "AI-ассистент под ключ ⭐", "description": "Консультация + создание персонального AI-ассистента", "stars": STARS_CUSTOM, "days": 0},
    "cu_activation": {"title": "AI Computer Use — Активация ⭐", "description": "Подключение AI + первый месяц бесплатно", "stars": STARS_CU_ACTIVATION, "days": 30},
    "starter": {"title": "AI Centers Starter", "description": "1 AI-сотрудник • Telegram + WhatsApp + сайт • Обучение на ваших данных", "stars": STARS_STARTER, "days": 30},
    "pro": {"title": "AI Centers Pro", "description": "3 AI-сотрудника • Все каналы • CRM интеграция • Аналитика", "stars": STARS_PRO, "days": 30},
    "business": {"title": "AI Centers Business", "description": "10 AI-сотрудников • API + webhook • White Label • Приоритет", "stars": STARS_BUSINESS, "days": 30},
    "enterprise": {"title": "AI Centers Enterprise", "description": "Безлимит AI-сотрудников • Все каналы + голос • CRM • API • White Label • Выделенный сервер", "stars": STARS_ENTERPRISE, "days": 30},
}

# ── Feature matrix per plan ──
PLAN_FEATURES = {
    "starter": {
        "bots": 1,
        "channels": ["telegram", "whatsapp", "website"],
        "voice": False,
        "crm": False,
        "api": False,
        "white_label": False,
        "analytics": False,
        "priority_support": False,
        "monthly_stars": 950,    # $19/мес
        "label": "Starter",
        "price_setup": "$149",
        "price_monthly": "$19/мес",
    },
    "pro": {
        "bots": 3,
        "channels": ["telegram", "whatsapp", "website", "instagram"],
        "voice": False,
        "crm": True,
        "api": False,
        "white_label": False,
        "analytics": True,
        "priority_support": True,
        "monthly_stars": 2450,   # $49/мес
        "label": "Pro",
        "price_setup": "$299",
        "price_monthly": "$49/мес",
    },
    "business": {
        "bots": 10,
        "channels": ["telegram", "whatsapp", "website", "instagram"],
        "voice": True,
        "crm": True,
        "api": True,
        "white_label": True,
        "analytics": True,
        "priority_support": True,
        "monthly_stars": 3950,   # $79/мес
        "label": "Business",
        "price_setup": "$499",
        "price_monthly": "$79/мес",
    },
    "enterprise": {
        "bots": 999,
        "channels": ["telegram", "whatsapp", "website", "instagram", "phone"],
        "voice": True,
        "crm": True,
        "api": True,
        "white_label": True,
        "analytics": True,
        "priority_support": True,
        "monthly_stars": 9950,   # $199/мес
        "label": "Enterprise",
        "price_setup": "$1499",
        "price_monthly": "$199/мес",
    },
}

def get_plan_features(plan_key: str) -> dict:
    """Get features for a plan, defaulting to starter."""
    return PLAN_FEATURES.get(plan_key, PLAN_FEATURES["starter"])

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


@router.pre_checkout_query()
async def on_pre_checkout(query: types.PreCheckoutQuery):
    await query.answer(ok=True)


@router.message(F.successful_payment)
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
        from handlers.computer_use import activate_cu; await activate_cu(message, uid, user, stars)
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
    session["plan"] = plan_key

    # Show what's included in this plan
    features = get_plan_features(plan_key)
    feature_lines = []
    feature_lines.append(f"👥 AI-сотрудников: <b>{'безлимит' if features['bots'] >= 999 else features['bots']}</b>")
    ch_names = {"telegram": "Telegram", "whatsapp": "WhatsApp", "website": "Сайт", "instagram": "Instagram", "phone": "📞 Телефон"}
    ch_list = ", ".join(ch_names.get(c, c) for c in features["channels"])
    feature_lines.append(f"📱 Каналы: <b>{ch_list}</b>")
    if features["voice"]:
        feature_lines.append("🗣 Голосовой AI-секретарь: ✅")
    if features["crm"]:
        feature_lines.append("📊 CRM интеграция: ✅")
    if features["api"]:
        feature_lines.append("🔌 API + Webhook: ✅")
    if features["white_label"]:
        feature_lines.append("🏷 White Label: ✅")

    await message.answer(
        f"📦 <b>Ваш план {features['label']}:</b>\n\n"
        + "\n".join(feature_lines) +
        "\n\nВсё это будет настроено автоматически! Начнём 👇"
    )

    ob_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍽 Ресторан / кафе", callback_data="ob_restaurant"),
         InlineKeyboardButton(text="🏥 Клиника", callback_data="ob_clinic")],
        [InlineKeyboardButton(text="💇 Салон красоты", callback_data="ob_salon"),
         InlineKeyboardButton(text="🛍 Магазин", callback_data="ob_shop")],
        [InlineKeyboardButton(text="💼 Услуги / B2B", callback_data="ob_services"),
         InlineKeyboardButton(text="📦 Другое", callback_data="ob_other")],
    ])

    total_steps = 4
    if features["voice"]:
        total_steps += 1
    if features["crm"]:
        total_steps += 1

    await message.answer(
        f"📋 <b>Шаг 1 из {total_steps} — Ваш бизнес</b>\n\n"
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
    except Exception: pass
    
    logger.info(f"Payment: {uid} paid {stars} stars for {plan_key}")


@router.callback_query(F.data == "pay_bank")
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

@router.callback_query(F.data.startswith("pay_"))
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


