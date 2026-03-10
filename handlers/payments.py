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


