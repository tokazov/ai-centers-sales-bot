"""Sales funnel: step1 display, business/leads selection, demo, pricing, buy."""

import logging
from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core import (
    bot, ADMIN_ID, get_session, detect_lang, t, send_with_voice, sessions,
    track_user,
)
from handlers.payments import send_stars_invoice

logger = logging.getLogger(__name__)
router = Router()

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


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    logger.info(f"CMD_START called for user {message.from_user.id}, payload: {message.text}")
    uid = message.from_user.id
    lang = detect_lang(message.from_user)
    sessions[uid] = {"history": [], "count": 0, "mode": "receptionist", "persona": None, "lang": lang, "funnel_shown": False, "funnel_step": None}
    
    # Track user in DB
    user = message.from_user
    track_user(uid, username=user.username, full_name=user.full_name, lang=lang)
    
    # Handle deep links: /start partner, /start buy_starter, etc.
    args = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
    
    if args == "partner":
        # Partner program registration
        partner_text = (
            "🤝 <b>Партнёрская программа AI Centers</b>\n\n"
            "Зарабатывайте <b>от 20% до 50%</b> с каждого клиента!\n\n"
            "📈 <b>Как это работает:</b>\n"
            "1. Вы рекомендуете AI Centers бизнесам\n"
            "2. Мы создаём и настраиваем AI-ассистента\n"
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
        # Save to DB
        from core import register_partner
        register_partner(uid, message.from_user.username, message.from_user.full_name)
        # Notify admin
        try:
            from core import get_partners_count
            total = get_partners_count()
            await bot.send_message(ADMIN_ID, f"🤝 Новый партнёр! #{total}\n@{message.from_user.username or '?'} ({message.from_user.full_name})\nID: {uid}")
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

@router.callback_query(F.data == "back_step1")
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
@router.callback_query(F.data.startswith("biz_"))
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

@router.callback_query(F.data.startswith("leads_"))
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
@router.callback_query(F.data == "funnel_demo")
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
    except Exception: pass


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

@router.callback_query(F.data == "funnel_pricing")
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
@router.callback_query(F.data.startswith("funnel_buy_"))
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
    except Exception: pass


# Step 5c — Question → Gemini handles objections, then returns to offer
@router.callback_query(F.data == "funnel_question")
async def on_funnel_question(callback: types.CallbackQuery):
    uid = callback.from_user.id
    session = get_session(uid)
    session["mode"] = "objection_handler"
    lang = session.get("lang", detect_lang(callback.from_user))

    await callback.message.edit_text(t(lang, "ask_question"))
    await callback.answer()



