"""Computer Use funnel: pilot, questionnaire, pricing, activation, demo."""

import os
import json
import logging
import urllib.request
from aiogram import Router, F, types
import aiohttp
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import aiohttp

from core import (
    bot, ADMIN_ID, PLATFORM_API_URL, PLATFORM_API_KEY, COMPUTER_USE_BOT,
    get_session, detect_lang, t, gemini_chat,
)

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(F.data == "biz_computer")
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


@router.callback_query(F.data == "cu_funnel_pilot")
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


@router.callback_query(F.data == "cu_start_questionnaire")
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


@router.callback_query(F.data == "cu_funnel_pricing")
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


@router.callback_query(F.data == "cu_funnel_question")
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
@router.callback_query(F.data == "pay_cu_activation_stars")
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
            "Напишите AI-ассистенту — он уже готов работать:\n"
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


