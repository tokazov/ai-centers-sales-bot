#!/usr/bin/env python3
"""
AI Centers Sales Bot v2.0
Telegram бот для продажи AI-ассистентов для бизнеса.
Поддерживает: URL auto-setup, текстовый онбординг, Stars оплата, BotFather интеграция.
"""

import os
import json
import logging
import asyncio
import re
from datetime import datetime
from typing import Optional

from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    LabeledPrice, PreCheckoutQuery
)
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
import google.generativeai as genai
import aiohttp

# ─── Logging ───
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ─── Config ───
BOT_TOKEN = os.getenv("BOT_TOKEN", "placeholder_token")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "5309206282"))
PLATFORM_API_URL = os.getenv("PLATFORM_API_URL", "https://platform-api-production-f313.up.railway.app")
LEADS_FILE = "leads.json"

# ─── Gemini ───
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-2.5-flash')

SALES_PROMPT = """Ты — консультант AI Centers. Помогаешь бизнесу получить AI-ассистента.

КЛЮЧЕВОЕ ПРЕДЛОЖЕНИЕ:
- Создание AI-бота: от $99 (разово) + от $15/мес (абонплата)
- Работает 24/7, отвечает клиентам, записывает на услуги
- Настройка за 5 минут если есть сайт, или за 24 часа по описанию
- Дешевле сотрудника в 50 раз

ТВОЯ ЗАДАЧА: выяснить что за бизнес, предложить подходящий тариф, привести к оплате.
Если клиент скинул URL сайта — предложи auto-setup (бот за 5 минут).
Определи язык клиента и отвечай на нём. Будь конкретным, не лей воду."""

# ─── FSM States ───
class ContactForm(StatesGroup):
    waiting_for_name = State()
    waiting_for_business = State()
    waiting_for_niche = State()
    waiting_for_contact = State()

class Onboarding(StatesGroup):
    waiting_for_business_name = State()
    waiting_for_niche = State()
    waiting_for_description = State()
    waiting_for_phone = State()
    waiting_for_address = State()
    waiting_for_schedule = State()
    waiting_for_services = State()
    waiting_for_bot_token = State()

class URLSetup(StatesGroup):
    waiting_for_url_confirm = State()
    waiting_for_plan_select = State()
    waiting_for_bot_token = State()

# ─── Plans (DUAL PRICING — creation + subscription) ───
PLANS = {
    "starter": {
        "name": "Starter",
        "creation_price": "$99",
        "monthly_price": "$15/мес",
        "stars_creation": 1000,
        "stars_monthly": 150,
        "features": [
            "✓ 1 AI-агент",
            "✓ Telegram канал",
            "✓ База знаний из сайта",
            "✓ Безлимит сообщений"
        ]
    },
    "pro": {
        "name": "Pro",
        "creation_price": "$199",
        "monthly_price": "$29/мес",
        "stars_creation": 2000,
        "stars_monthly": 300,
        "badge": "⭐ Популярный",
        "features": [
            "✓ 3 AI-агента",
            "✓ Мультиканал (TG + WA + IG)",
            "✓ CRM интеграция",
            "✓ Аналитика и статистика",
            "✓ Приоритетная поддержка"
        ]
    },
    "business": {
        "name": "Business",
        "creation_price": "$399",
        "monthly_price": "$59/мес",
        "stars_creation": 4000,
        "stars_monthly": 600,
        "features": [
            "✓ 10 AI-агентов",
            "✓ Голосовой AI",
            "✓ Белый лейбл",
            "✓ Персональный менеджер",
            "✓ SLA гарантия"
        ]
    },
    "enterprise": {
        "name": "Enterprise",
        "creation_price": "от $999",
        "monthly_price": "$149/мес",
        "stars_creation": 10000,
        "stars_monthly": 1500,
        "features": [
            "✓ Безлимит агентов",
            "✓ Свой API ключ",
            "✓ Любые интеграции",
            "✓ Выделенный менеджер",
            "✓ SLA 99.9%"
        ]
    }
}

NICHES = [
    ("restaurant", "🍽 Ресторан"),
    ("salon", "💇 Салон"),
    ("delivery", "🚚 Доставка"),
    ("hotel", "🏨 Отель"),
    ("fitness", "💪 Фитнес"),
    ("clinic", "⚕️ Клиника"),
    ("realestate", "🏠 Недвижимость"),
    ("education", "📚 Образование"),
    ("other", "📝 Другое")
]

FAQ_ANSWERS = {
    "how_it_works": """🔧 <b>Как это работает?</b>

<b>Способ 1 — Автоматически (5 минут):</b>
1. Скиньте ссылку на ваш сайт
2. AI проанализирует бизнес
3. Оплатите тариф
4. Получите готового бота!

<b>Способ 2 — Вручную (24 часа):</b>
1. Выберите тариф и оплатите
2. Заполните информацию о бизнесе
3. Наш AI создаёт бота
4. Тестируете и запускаете

Бот отвечает клиентам 24/7, записывает на услуги, консультирует.""",
    
    "pricing": """💰 <b>Тарифы (создание + абонплата):</b>

📦 <b>Starter</b> — $99 + $15/мес
1 бот, Telegram, безлимит сообщений

📦 <b>Pro</b> — $199 + $29/мес ⭐
3 бота, мультиканал, CRM, аналитика

📦 <b>Business</b> — $399 + $59/мес
10 ботов, голосовой AI, белый лейбл

📦 <b>Enterprise</b> — от $999 + $149/мес
Безлимит, API, любые интеграции

Без скрытых платежей. Гарантия 50% автоматизации или возврат.""",
    
    "speed": """⚡ <b>Как быстро запустите?</b>

🚀 <b>Есть сайт?</b> → 5 минут! Скиньте ссылку — бот проанализирует и создаст AI-ассистента автоматически.

📝 <b>Нет сайта?</b> → 24 часа. Заполните анкету, мы всё настроим.

Поддержка 24/7 на всех тарифах.""",
    
    "niches": """🎯 <b>Какие ниши?</b>

Готовые шаблоны:
• 🦷 Стоматология
• 🍽 Рестораны и кафе
• 💇 Салоны красоты
• 🏠 Недвижимость
• 💪 Фитнес-клубы
• 🏨 Отели
• 🚚 Доставка
• ⚕️ Клиники

Но мы настраиваем под <b>любой бизнес</b> — автосервис, юристы, магазины, школы.

AI учится на вашем сайте или описании за минуты.""",
    
    "guarantee": """🛡 <b>Гарантия качества</b>

✅ <b>50% автоматизации или возврат</b>
Если бот за 30 дней не решает 50% обращений автоматически — возвращаем деньги.

✅ Без скрытых платежей
✅ Мгновенная отмена подписки
✅ Уведомление за 3 дня до списания
✅ Экспорт данных в любой момент
✅ Без автоповышения тарифа

Подробнее: aicenters.co/pricing-promise"""
}


# ─── Bot Init ───
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()


# ─── Helpers ───
def save_lead(lead_data: dict):
    leads = []
    if os.path.exists(LEADS_FILE):
        with open(LEADS_FILE, 'r', encoding='utf-8') as f:
            try: leads = json.load(f)
            except: leads = []
    lead_data['timestamp'] = datetime.now().isoformat()
    leads.append(lead_data)
    with open(LEADS_FILE, 'w', encoding='utf-8') as f:
        json.dump(leads, f, ensure_ascii=False, indent=2)


def is_url(text: str) -> bool:
    """Check if text looks like a URL."""
    return bool(re.match(r'^https?://[^\s<>"\']+$', text.strip()))


async def scrape_preview(url: str) -> Optional[dict]:
    """Quick scrape to show client what we found on their site."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10),
                                   headers={"User-Agent": "Mozilla/5.0 (compatible; AICentersBot/1.0)"}) as resp:
                if resp.status != 200:
                    return None
                html = await resp.text()
        
        # Extract title
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else url
        
        # Extract meta description
        desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)', html, re.IGNORECASE)
        if not desc_match:
            desc_match = re.search(r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*name=["\']description', html, re.IGNORECASE)
        description = desc_match.group(1).strip()[:200] if desc_match else ""
        
        # Extract phone numbers
        phones = re.findall(r'[\+]?[0-9\s\-\(\)]{7,15}', html)
        phones = list(set([p.strip() for p in phones if len(p.strip()) >= 7]))[:3]
        
        # Count text length (rough content size indicator)
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', text).strip()
        text_len = len(text)
        
        return {
            "title": title[:100],
            "description": description,
            "phones": phones,
            "text_length": text_len,
            "url": url
        }
    except Exception as e:
        logger.error(f"Scrape preview failed for {url}: {e}")
        return None


# ─── Keyboards ───
def get_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 У меня есть сайт — создать бота за 5 мин", callback_data="url_setup")],
        [InlineKeyboardButton(text="🎯 Попробовать демо", callback_data="demo")],
        [InlineKeyboardButton(text="💰 Тарифы", callback_data="pricing")],
        [InlineKeyboardButton(text="📞 Связаться", callback_data="contact")],
        [InlineKeyboardButton(text="❓ FAQ", callback_data="faq")]
    ])


def get_pricing_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Starter — $99 + $15/мес", callback_data="buy_starter")],
        [InlineKeyboardButton(text=f"Pro — $199 + $29/мес ⭐", callback_data="buy_pro")],
        [InlineKeyboardButton(text=f"Business — $399 + $59/мес", callback_data="buy_business")],
        [InlineKeyboardButton(text=f"Enterprise — от $999", callback_data="buy_enterprise")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
    ])


def get_plan_select_keyboard():
    """Keyboard for URL setup plan selection."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Starter — $99 + $15/мес", callback_data="urlplan_starter")],
        [InlineKeyboardButton(text="Pro — $199 + $29/мес ⭐", callback_data="urlplan_pro")],
        [InlineKeyboardButton(text="Business — $399 + $59/мес", callback_data="urlplan_business")],
        [InlineKeyboardButton(text="Enterprise — от $999", callback_data="urlplan_enterprise")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
    ])


def get_niche_keyboard():
    buttons = [[InlineKeyboardButton(text=name, callback_data=f"niche_{code}")] for code, name in NICHES]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_faq_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Как это работает?", callback_data="faq_how_it_works")],
        [InlineKeyboardButton(text="Сколько стоит?", callback_data="faq_pricing")],
        [InlineKeyboardButton(text="Как быстро запустите?", callback_data="faq_speed")],
        [InlineKeyboardButton(text="Какие ниши?", callback_data="faq_niches")],
        [InlineKeyboardButton(text="Гарантия качества", callback_data="faq_guarantee")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
    ])


def get_back_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_menu")]
    ])


def get_botfather_keyboard():
    """Keyboard with BotFather link + skip."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Открыть @BotFather", url="https://t.me/BotFather")],
        [InlineKeyboardButton(text="⏩ Пропустить — создайте за меня", callback_data="skip_bot_token")],
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="back_to_menu")]
    ])


# ─── /start ───
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        param = args[1]
        
        # Partner referral link: /start ref_XXXXXXXX
        if param.startswith("ref_"):
            ref_code = param.replace("ref_", "")
            await state.update_data(ref_code=ref_code)
            logger.info(f"Referral from partner: {ref_code}, user: {message.from_user.id}")
        
        # Direct buy deeplink: /start buy_starter
        if param.startswith("buy_"):
            plan_id = param.replace("buy_", "")
            plan = PLANS.get(plan_id)
            if plan:
                prices = [LabeledPrice(label=f"Создание {plan['name']}", amount=plan['stars_creation'])]
                desc = f"{plan['name']} — {plan['creation_price']} разово + {plan['monthly_price']}\n" + "\n".join(plan['features'])
                try:
                    await bot.send_invoice(
                        chat_id=message.chat.id, title=f"AI Centers — {plan['name']}",
                        description=desc, payload=f"plan_{plan_id}",
                        provider_token="", currency="XTR", prices=prices
                    )
                    return
                except Exception as e:
                    logger.error(f"Deeplink invoice error: {e}")
        
        # Partner registration: /start partner
        if param == "partner":
            await message.answer(
                "🤝 <b>Партнёрская программа AI Centers</b>\n\n"
                "Зарабатывайте 20-50% с каждого клиента!\n\n"
                "🥉 Bronze: 20% (старт)\n"
                "🥈 Silver: 35% (от 5 продаж)\n"
                "🥇 Gold: 50% (от 15 продаж)\n\n"
                "📊 Подробнее: aicenters.co/partners\n\n"
                "Чтобы стать партнёром, нажмите кнопку:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="✅ Стать партнёром", callback_data="become_partner")],
                    [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
                ])
            )
            return
    
    welcome = """👋 <b>AI Centers</b> — создаём AI-ассистентов для бизнеса.

🌐 <b>Есть сайт?</b> Скиньте ссылку — бот будет готов за 5 минут!

Или выберите действие:"""
    
    await message.answer(welcome, reply_markup=get_main_menu())


# ─── URL Auto-Setup Flow ───

@router.callback_query(F.data == "url_setup")
async def url_setup_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🌐 <b>Автоматическое создание бота</b>\n\n"
        "Отправьте ссылку на ваш сайт.\n"
        "AI проанализирует бизнес и создаст бота с полной базой знаний.\n\n"
        "Пример: <code>https://example.com</code>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
        ])
    )
    await state.set_state(URLSetup.waiting_for_url_confirm)
    await callback.answer()


@router.message(StateFilter(URLSetup.waiting_for_url_confirm))
async def url_setup_received(message: Message, state: FSMContext):
    """Client sent a URL — scrape preview and confirm."""
    url = message.text.strip()
    
    if not is_url(url):
        await message.answer(
            "❌ Это не похоже на ссылку. Отправьте URL в формате:\n"
            "<code>https://example.com</code>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
            ])
        )
        return
    
    await message.answer("⏳ Анализирую сайт...")
    await bot.send_chat_action(message.chat.id, "typing")
    
    preview = await scrape_preview(url)
    
    if not preview or preview["text_length"] < 100:
        await message.answer(
            "😕 Не удалось прочитать сайт. Возможно он защищён или не загружается.\n\n"
            "Вы можете:\n"
            "• Попробовать другую ссылку\n"
            "• Или описать бизнес вручную — мы создадим бота за 24 часа",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📝 Описать вручную", callback_data="contact")],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
            ])
        )
        return
    
    # Save URL for later
    await state.update_data(url=url, site_title=preview["title"])
    
    phones_text = ", ".join(preview["phones"]) if preview["phones"] else "не найдены"
    
    preview_text = f"""✅ <b>Сайт проанализирован!</b>

🏢 <b>{preview['title']}</b>
📝 {preview['description'][:150] + '...' if len(preview['description']) > 150 else preview['description']}
📞 Телефоны: {phones_text}
📊 Контент: {preview['text_length']:,} символов

AI создаст бота на основе всей информации с сайта:
• Услуги и цены
• Контакты и адрес
• FAQ и описание
• Расписание работы

<b>Выберите тариф для создания:</b>"""
    
    await message.answer(preview_text, reply_markup=get_plan_select_keyboard())
    await state.set_state(URLSetup.waiting_for_plan_select)


@router.callback_query(StateFilter(URLSetup.waiting_for_plan_select), F.data.startswith("urlplan_"))
async def url_plan_selected(callback: CallbackQuery, state: FSMContext):
    """Plan selected for URL setup — send invoice."""
    plan_id = callback.data.replace("urlplan_", "")
    plan = PLANS.get(plan_id)
    if not plan:
        await callback.answer("❌ Тариф не найден", show_alert=True)
        return
    
    await state.update_data(plan=plan_id)
    
    prices = [LabeledPrice(label=f"Создание {plan['name']}", amount=plan['stars_creation'])]
    desc = f"{plan['name']} — {plan['creation_price']} разово\n+ {plan['monthly_price']} абонплата\n\n" + "\n".join(plan['features'])
    
    try:
        await bot.send_invoice(
            chat_id=callback.message.chat.id,
            title=f"AI Centers — {plan['name']}",
            description=desc,
            payload=f"url_plan_{plan_id}",
            provider_token="",
            currency="XTR",
            prices=prices
        )
        await callback.answer("✨ Создан счёт на оплату")
    except Exception as e:
        logger.error(f"URL plan invoice error: {e}")
        await callback.answer("❌ Ошибка. Попробуйте позже.", show_alert=True)


# ─── Callbacks ───

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    welcome = """👋 <b>AI Centers</b> — создаём AI-ассистентов для бизнеса.

🌐 <b>Есть сайт?</b> Скиньте ссылку — бот будет готов за 5 минут!

Или выберите действие:"""
    await callback.message.edit_text(welcome, reply_markup=get_main_menu())
    await callback.answer()


@router.callback_query(F.data == "demo")
async def show_demo(callback: CallbackQuery):
    await callback.message.edit_text(
        "🎯 <b>Попробуйте демо-ботов!</b>\n\n"
        "👉 @aicenters_demo_bot\n\n"
        "Выберите нишу (ресторан, клиника, салон) и пообщайтесь как клиент.\n"
        "Такой же бот будет у вас — только настроенный под ваш бизнес!",
        reply_markup=get_back_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "pricing")
async def show_pricing(callback: CallbackQuery):
    text = "💰 <b>Тарифы (создание + абонплата):</b>\n\n"
    for pid, plan in PLANS.items():
        text += f"━━━━━━━━━━━━━━━\n"
        text += f"📦 <b>{plan['name']}</b>"
        if "badge" in plan:
            text += f" {plan['badge']}"
        text += f"\n💵 {plan['creation_price']} разово + {plan['monthly_price']}\n\n"
        text += "\n".join(plan['features'])
        text += "\n\n"
    text += "━━━━━━━━━━━━━━━\n🛡 Гарантия 50% автоматизации или возврат"
    await callback.message.edit_text(text, reply_markup=get_pricing_keyboard())
    await callback.answer()


@router.callback_query(F.data == "contact")
async def start_contact_form(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📝 Давайте познакомимся.\n\n<b>Как вас зовут?</b>")
    await state.set_state(ContactForm.waiting_for_name)
    await callback.answer()


@router.callback_query(F.data == "faq")
async def show_faq(callback: CallbackQuery):
    await callback.message.edit_text("❓ <b>Часто задаваемые вопросы:</b>", reply_markup=get_faq_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("faq_"))
async def show_faq_answer(callback: CallbackQuery):
    qid = callback.data.replace("faq_", "")
    answer = FAQ_ANSWERS.get(qid, "Ответ не найден")
    await callback.message.edit_text(answer, reply_markup=get_back_keyboard())
    await callback.answer()


# ─── Contact Form ───

@router.message(StateFilter(ContactForm.waiting_for_name))
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("<b>Как называется ваш бизнес?</b>")
    await state.set_state(ContactForm.waiting_for_business)

@router.message(StateFilter(ContactForm.waiting_for_business))
async def process_business(message: Message, state: FSMContext):
    await state.update_data(business=message.text)
    await message.answer("<b>В какой нише?</b>", reply_markup=get_niche_keyboard())
    await state.set_state(ContactForm.waiting_for_niche)

@router.callback_query(StateFilter(ContactForm.waiting_for_niche), F.data.startswith("niche_"))
async def process_niche(callback: CallbackQuery, state: FSMContext):
    niche_code = callback.data.replace("niche_", "")
    niche_name = next((name for code, name in NICHES if code == niche_code), "Неизвестно")
    await state.update_data(niche=niche_name)
    await callback.message.edit_text("<b>Как с вами связаться?</b>\n\nТелефон или @username:")
    await state.set_state(ContactForm.waiting_for_contact)
    await callback.answer()

@router.message(StateFilter(ContactForm.waiting_for_contact))
async def process_contact(message: Message, state: FSMContext):
    data = await state.get_data()
    data['contact'] = message.text
    data['user_id'] = message.from_user.id
    data['username'] = message.from_user.username
    save_lead(data)
    
    admin_msg = (f"🆕 <b>Новая заявка!</b>\n\n"
                 f"👤 {data['name']}\n🏢 {data['business']}\n"
                 f"🎯 {data['niche']}\n📞 {data['contact']}\n"
                 f"🆔 {data['user_id']} @{data.get('username', '')}")
    try:
        await bot.send_message(ADMIN_CHAT_ID, admin_msg)
    except: pass
    
    await message.answer(
        f"✅ <b>Спасибо, {data['name']}!</b>\n\n"
        f"Заявка принята. Свяжемся с вами через {data['contact']}.\n\n"
        f"А пока — посмотрите тарифы или попробуйте демо!",
        reply_markup=get_main_menu()
    )
    await state.clear()


# ─── Payment Processing ───

@router.callback_query(F.data.startswith("buy_"))
async def process_payment(callback: CallbackQuery, state: FSMContext):
    plan_id = callback.data.replace("buy_", "")
    plan = PLANS.get(plan_id)
    if not plan:
        await callback.answer("❌ Тариф не найден", show_alert=True)
        return
    
    await state.update_data(plan=plan_id)
    
    prices = [LabeledPrice(label=f"Создание {plan['name']}", amount=plan['stars_creation'])]
    desc = f"{plan['name']} — {plan['creation_price']} + {plan['monthly_price']}\n" + "\n".join(plan['features'])
    
    try:
        await bot.send_invoice(
            chat_id=callback.message.chat.id,
            title=f"AI Centers — {plan['name']}",
            description=desc,
            payload=f"plan_{plan_id}",
            provider_token="",
            currency="XTR",
            prices=prices
        )
        await callback.answer("✨ Создан счёт")
    except Exception as e:
        logger.error(f"Invoice error: {e}")
        await callback.answer("❌ Ошибка. Попробуйте позже.", show_alert=True)


@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(message: Message, state: FSMContext):
    payment = message.successful_payment
    payload = payment.invoice_payload
    
    # Determine plan
    if payload.startswith("url_plan_"):
        plan_id = payload.replace("url_plan_", "")
    else:
        plan_id = payload.replace("plan_", "")
    
    plan = PLANS.get(plan_id, PLANS["starter"])
    data = await state.get_data()
    
    # Track partner referral if exists
    ref_code = data.get("ref_code")
    if ref_code:
        await track_partner_referral(ref_code, message.from_user, plan_id, plan['stars_creation'])
    
    # Admin notification
    ref_info = f"\n🤝 Реферал: {ref_code}" if ref_code else ""
    admin_msg = (f"💰 <b>Оплата!</b>\n\n"
                 f"📦 {plan['name']} ({plan['stars_creation']} Stars)\n"
                 f"👤 {message.from_user.full_name}\n"
                 f"🆔 {message.from_user.id} @{message.from_user.username or ''}{ref_info}")
    try:
        await bot.send_message(ADMIN_CHAT_ID, admin_msg)
    except: pass
    
    # URL-based setup — skip onboarding, go straight to bot token
    if payload.startswith("url_plan_") and data.get("url"):
        await message.answer(
            f"🎉 <b>Оплата прошла! Тариф: {plan['name']}</b>\n\n"
            f"Последний шаг — нужен Telegram-бот.\n\n"
            f"1. Откройте @BotFather\n"
            f"2. Отправьте /newbot\n"
            f"3. Придумайте имя (например: <i>{data.get('site_title', 'MyBusiness')} Assistant</i>)\n"
            f"4. Скопируйте токен и отправьте сюда\n\n"
            f"Или нажмите «Пропустить» — мы создадим бота за вас.",
            reply_markup=get_botfather_keyboard()
        )
        await state.update_data(plan=plan_id, flow="url")
        await state.set_state(URLSetup.waiting_for_bot_token)
        return
    
    # Standard onboarding flow
    await message.answer(
        f"🎉 <b>Оплата прошла! Тариф: {plan['name']}</b>\n\n"
        f"Сейчас соберём информацию для вашего AI-ассистента.\n\n"
        f"<b>Название вашего бизнеса?</b>"
    )
    await state.update_data(plan=plan_id, flow="manual")
    await state.set_state(Onboarding.waiting_for_business_name)


# ─── URL Setup: Bot Token ───

@router.message(StateFilter(URLSetup.waiting_for_bot_token))
async def url_bot_token_received(message: Message, state: FSMContext):
    """Client sent bot token for URL setup."""
    token = message.text.strip()
    
    # Validate token format
    if not re.match(r'^\d+:[A-Za-z0-9_-]{30,50}$', token):
        await message.answer(
            "❌ Это не похоже на токен бота.\n\n"
            "Токен выглядит так: <code>123456789:ABCdefGHIjklMNOpqrsTUVwxyz</code>\n\n"
            "Получите его у @BotFather → /newbot",
            reply_markup=get_botfather_keyboard()
        )
        return
    
    data = await state.get_data()
    url = data.get("url", "")
    plan_id = data.get("plan", "starter")
    
    await message.answer("⏳ <b>Создаю AI-ассистента из вашего сайта...</b>\n\nЭто займёт 1-2 минуты.")
    await bot.send_chat_action(message.chat.id, "typing")
    
    # Call Platform API auto-setup
    success = await create_bot_from_url(message, token, url, data.get("site_title", ""), plan_id)
    
    if not success:
        # Fallback: notify admin for manual creation
        await message.answer(
            "⚠️ Автоматическое создание не удалось.\n\n"
            "Наш специалист создаст бота в течение <b>2 часов</b>.\n"
            "Вы получите ссылку прямо сюда.",
            reply_markup=get_main_menu()
        )
        await bot.send_message(ADMIN_CHAT_ID,
            f"⚠️ <b>Auto-setup FAILED — вручную!</b>\n\n"
            f"👤 {message.from_user.full_name} ({message.from_user.id})\n"
            f"🌐 {url}\n📦 {plan_id}\n🔑 Токен получен")
    
    await state.clear()


@router.callback_query(F.data == "skip_bot_token")
async def skip_bot_token(callback: CallbackQuery, state: FSMContext):
    """Client doesn't want to create bot themselves."""
    data = await state.get_data()
    
    await callback.message.edit_text(
        "✅ <b>Принято!</b>\n\n"
        "Наш специалист создаст Telegram-бота и настроит AI-ассистента "
        "на основе вашего сайта в течение <b>2 часов</b>.\n\n"
        "Вы получите ссылку на готового бота прямо сюда.",
        reply_markup=get_main_menu()
    )
    
    await bot.send_message(ADMIN_CHAT_ID,
        f"🔧 <b>Нужно создать бота вручную</b>\n\n"
        f"👤 {callback.from_user.full_name} ({callback.from_user.id})\n"
        f"🌐 {data.get('url', '—')}\n"
        f"📦 {data.get('plan', 'starter')}\n"
        f"💰 Оплачено Stars\n"
        f"⚠️ Клиент не создал бота в BotFather")
    
    await state.clear()
    await callback.answer()


async def create_bot_from_url(message: Message, bot_token: str, url: str, site_title: str, plan_id: str) -> bool:
    """Create bot via Platform API auto-setup endpoint."""
    try:
        async with aiohttp.ClientSession() as session:
            # First authenticate to get JWT
            auth_resp = await session.post(
                f"{PLATFORM_API_URL}/auth/telegram",
                json={
                    "id": message.from_user.id,
                    "first_name": message.from_user.first_name or "",
                    "last_name": message.from_user.last_name or "",
                    "username": message.from_user.username or "",
                    "photo_url": "",
                    "auth_date": int(datetime.now().timestamp()),
                    "hash": "sales_bot_internal"
                },
                timeout=aiohttp.ClientTimeout(total=10)
            )
            
            if auth_resp.status != 200:
                logger.error(f"Auth failed: {auth_resp.status}")
                return False
            
            auth_data = await auth_resp.json()
            jwt_token = auth_data.get("access_token", "")
            
            # Call auto-setup
            setup_resp = await session.post(
                f"{PLATFORM_API_URL}/bots/auto-setup",
                json={
                    "bot_token": bot_token,
                    "url": url,
                    "language": "ru"
                },
                headers={"Authorization": f"Bearer {jwt_token}"},
                timeout=aiohttp.ClientTimeout(total=120)
            )
            
            if setup_resp.status == 201:
                result = await setup_resp.json()
                bot_username = result.get("bot_username", "")
                
                await message.answer(
                    f"🎉 <b>AI-ассистент готов!</b>\n\n"
                    f"🏢 {site_title}\n"
                    f"🤖 Бот: @{bot_username}\n"
                    f"🔗 https://t.me/{bot_username}\n\n"
                    f"<b>Что дальше:</b>\n"
                    f"1. Откройте бота и протестируйте\n"
                    f"2. Отправьте ссылку клиентам\n"
                    f"3. Добавьте на сайт (виджет)\n\n"
                    f"Нужны правки? Пишите — доработаем!",
                    reply_markup=get_main_menu()
                )
                
                await bot.send_message(ADMIN_CHAT_ID,
                    f"🤖 <b>Бот создан автоматически!</b>\n\n"
                    f"👤 {message.from_user.full_name}\n"
                    f"🌐 {url}\n"
                    f"🤖 @{bot_username}\n"
                    f"📦 {plan_id}")
                return True
            else:
                error = await setup_resp.text()
                logger.error(f"Auto-setup API error {setup_resp.status}: {error}")
                return False
                
    except Exception as e:
        logger.error(f"create_bot_from_url failed: {e}")
        return False


# ─── Standard Onboarding (after payment, no URL) ───

@router.message(StateFilter(Onboarding.waiting_for_business_name))
async def onboarding_business(message: Message, state: FSMContext):
    await state.update_data(business_name=message.text)
    await message.answer("<b>В какой нише?</b>", reply_markup=get_niche_keyboard())
    await state.set_state(Onboarding.waiting_for_niche)

@router.callback_query(StateFilter(Onboarding.waiting_for_niche), F.data.startswith("niche_"))
async def onboarding_niche(callback: CallbackQuery, state: FSMContext):
    niche_code = callback.data.replace("niche_", "")
    niche_name = next((name for code, name in NICHES if code == niche_code), "Неизвестно")
    await state.update_data(niche=niche_name)
    await callback.message.edit_text(
        "<b>Расскажите о бизнесе:</b>\n\n"
        "• Что предлагаете\n• Основные услуги\n• Что важно знать клиентам"
    )
    await state.set_state(Onboarding.waiting_for_description)
    await callback.answer()

@router.message(StateFilter(Onboarding.waiting_for_description))
async def onboarding_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("📞 <b>Контактный телефон:</b>\n\nНапример: +995 555 123456")
    await state.set_state(Onboarding.waiting_for_phone)

@router.message(StateFilter(Onboarding.waiting_for_phone))
async def onboarding_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("📍 <b>Адрес:</b>\n\nЕсли онлайн — напишите «онлайн»")
    await state.set_state(Onboarding.waiting_for_address)

@router.message(StateFilter(Onboarding.waiting_for_address))
async def onboarding_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    await message.answer("🕐 <b>Режим работы:</b>\n\nНапример: Пн-Пт 9:00-18:00")
    await state.set_state(Onboarding.waiting_for_schedule)

@router.message(StateFilter(Onboarding.waiting_for_schedule))
async def onboarding_schedule(message: Message, state: FSMContext):
    await state.update_data(schedule=message.text)
    await message.answer(
        "📋 <b>Основные услуги/товары с ценами:</b>\n\n"
        "По одной на строку:\n"
        "<i>Стрижка мужская — 30 лари\nМаникюр — 40 лари</i>"
    )
    await state.set_state(Onboarding.waiting_for_services)

@router.message(StateFilter(Onboarding.waiting_for_services))
async def onboarding_services(message: Message, state: FSMContext):
    await state.update_data(services_raw=message.text)
    
    await message.answer(
        "🤖 <b>Последний шаг — Telegram-бот</b>\n\n"
        "1. Откройте @BotFather\n"
        "2. Отправьте /newbot\n"
        "3. Придумайте имя\n"
        "4. Скопируйте токен и отправьте сюда\n\n"
        "Или нажмите «Пропустить».",
        reply_markup=get_botfather_keyboard()
    )
    await state.set_state(Onboarding.waiting_for_bot_token)


@router.message(StateFilter(Onboarding.waiting_for_bot_token))
async def onboarding_bot_token(message: Message, state: FSMContext):
    """Client sent bot token for manual onboarding."""
    token = message.text.strip()
    
    if not re.match(r'^\d+:[A-Za-z0-9_-]{30,50}$', token):
        await message.answer(
            "❌ Неверный формат токена.\n\n"
            "Токен: <code>123456789:ABCdefGHIjklMNOpqrsTUVwxyz</code>\n\n"
            "Получите у @BotFather → /newbot",
            reply_markup=get_botfather_keyboard()
        )
        return
    
    data = await state.get_data()
    plan_id = data.get("plan", "starter")
    
    await message.answer("⏳ <b>Создаю AI-ассистента...</b>\n\nЭто займёт 1-2 минуты.")
    await bot.send_chat_action(message.chat.id, "typing")
    
    # Build business text
    business_text = f"""
Бизнес: {data.get('business_name', '')}
Ниша: {data.get('niche', '')}
Описание: {data.get('description', '')}
Телефон: {data.get('phone', '')}
Адрес: {data.get('address', '')}
График: {data.get('schedule', '')}
Услуги:
{data.get('services_raw', '')}
"""
    
    try:
        async with aiohttp.ClientSession() as session:
            # Auth
            auth_resp = await session.post(
                f"{PLATFORM_API_URL}/auth/telegram",
                json={
                    "id": message.from_user.id,
                    "first_name": message.from_user.first_name or "",
                    "last_name": message.from_user.last_name or "",
                    "username": message.from_user.username or "",
                    "photo_url": "",
                    "auth_date": int(datetime.now().timestamp()),
                    "hash": "sales_bot_internal"
                },
                timeout=aiohttp.ClientTimeout(total=10)
            )
            auth_data = await auth_resp.json()
            jwt_token = auth_data.get("access_token", "")
            
            # Auto-setup from text
            setup_resp = await session.post(
                f"{PLATFORM_API_URL}/bots/auto-setup",
                json={
                    "bot_token": token,
                    "text": business_text,
                    "business_type": data.get("niche", ""),
                    "language": "ru"
                },
                headers={"Authorization": f"Bearer {jwt_token}"},
                timeout=aiohttp.ClientTimeout(total=120)
            )
            
            if setup_resp.status == 201:
                result = await setup_resp.json()
                bot_username = result.get("bot_username", "")
                
                await message.answer(
                    f"🎉 <b>AI-ассистент готов!</b>\n\n"
                    f"🏢 {data.get('business_name', '')}\n"
                    f"🤖 Бот: @{bot_username}\n"
                    f"🔗 https://t.me/{bot_username}\n\n"
                    f"<b>Что дальше:</b>\n"
                    f"1. Откройте бота и протестируйте\n"
                    f"2. Отправьте ссылку клиентам\n"
                    f"3. Добавьте на сайт\n\n"
                    f"Нужны правки? Пишите!",
                    reply_markup=get_main_menu()
                )
                
                await bot.send_message(ADMIN_CHAT_ID,
                    f"🤖 <b>Бот создан!</b>\n\n"
                    f"👤 {message.from_user.full_name}\n"
                    f"🏢 {data.get('business_name', '')}\n"
                    f"🤖 @{bot_username}\n📦 {plan_id}")
                
                await state.clear()
                return
            else:
                raise Exception(f"API {setup_resp.status}: {await setup_resp.text()}")
                
    except Exception as e:
        logger.error(f"Manual onboarding auto-setup failed: {e}")
    
    # Fallback
    services = []
    for line in (data.get('services_raw', '') or '').strip().split('\n'):
        line = line.strip()
        if line:
            sep = '—' if '—' in line else '-' if '-' in line else None
            if sep:
                parts = line.split(sep, 1)
                services.append({'name': parts[0].strip(), 'price': parts[1].strip() if len(parts) > 1 else ''})
            else:
                services.append({'name': line, 'price': ''})
    
    services_summary = '\n'.join([f"  • {s['name']}: {s['price']}" for s in services]) or 'Не указаны'
    
    await bot.send_message(ADMIN_CHAT_ID,
        f"⚠️ <b>Auto-setup FAILED — вручную!</b>\n\n"
        f"👤 {message.from_user.full_name} ({message.from_user.id})\n"
        f"🏢 {data.get('business_name', '')}\n"
        f"🎯 {data.get('niche', '')}\n"
        f"📝 {data.get('description', '')}\n"
        f"📞 {data.get('phone', '')}\n📍 {data.get('address', '')}\n"
        f"🕐 {data.get('schedule', '')}\n📋 Услуги:\n{services_summary}\n"
        f"📦 {plan_id}\n🔑 Токен: есть")
    
    await message.answer(
        f"✅ <b>Данные собраны!</b>\n\n"
        f"🏢 {data.get('business_name', '')}\n\n"
        f"Наш специалист создаст AI-ассистента в течение <b>2 часов</b>.\n"
        f"Ссылка на бота придёт сюда.",
        reply_markup=get_main_menu()
    )
    await state.clear()


@router.callback_query(StateFilter(Onboarding.waiting_for_bot_token), F.data == "skip_bot_token")
async def onboarding_skip_token(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    services_summary = data.get('services_raw', 'Не указаны')
    
    await bot.send_message(ADMIN_CHAT_ID,
        f"🔧 <b>Создать бота вручную</b>\n\n"
        f"👤 {callback.from_user.full_name} ({callback.from_user.id})\n"
        f"🏢 {data.get('business_name', '')}\n"
        f"🎯 {data.get('niche', '')}\n"
        f"📝 {data.get('description', '')}\n"
        f"📞 {data.get('phone', '')}\n📍 {data.get('address', '')}\n"
        f"🕐 {data.get('schedule', '')}\n📋 {services_summary}\n"
        f"📦 {data.get('plan', 'starter')}\n"
        f"⚠️ Клиент не создал бота")
    
    await callback.message.edit_text(
        "✅ <b>Принято!</b>\n\n"
        "Создадим бота и настроим AI-ассистента в течение <b>2 часов</b>.\n"
        "Ссылка придёт сюда.",
        reply_markup=get_main_menu()
    )
    await state.clear()
    await callback.answer()


# ─── AI Chat (free text → Gemini) ───
@router.message()
async def ai_chat(message: Message, state: FSMContext):
    """Handle free text — check if URL, otherwise AI chat."""
    text = message.text or ""
    
    # If it looks like a URL, start URL flow
    if is_url(text):
        await state.set_state(URLSetup.waiting_for_url_confirm)
        # Reuse the URL handler
        await url_setup_received(message, state)
        return
    
    # AI chat via Gemini
    try:
        await bot.send_chat_action(message.chat.id, "typing")
        chat = gemini_model.start_chat(history=[])
        response = await asyncio.to_thread(
            chat.send_message,
            f"{SALES_PROMPT}\n\nКлиент: {text}"
        )
        await message.answer(response.text, reply_markup=get_main_menu())
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        await message.answer(
            "Произошла ошибка. Выберите действие из меню:",
            reply_markup=get_main_menu()
        )


# ─── Partner Registration & Referral Tracking ───

@router.callback_query(F.data == "become_partner")
async def become_partner(callback: CallbackQuery):
    """Register user as partner via Platform API."""
    try:
        async with aiohttp.ClientSession() as session:
            # Auth first
            auth_resp = await session.post(
                f"{PLATFORM_API_URL}/auth/telegram",
                json={
                    "id": callback.from_user.id,
                    "first_name": callback.from_user.first_name or "",
                    "last_name": callback.from_user.last_name or "",
                    "username": callback.from_user.username or "",
                    "photo_url": "", "auth_date": int(datetime.now().timestamp()),
                    "hash": "sales_bot_internal"
                },
                timeout=aiohttp.ClientTimeout(total=10)
            )
            auth_data = await auth_resp.json()
            jwt = auth_data.get("access_token", "")
            
            # Register as partner
            resp = await session.post(
                f"{PLATFORM_API_URL}/partners/register",
                json={"name": callback.from_user.full_name, "telegram_id": callback.from_user.id},
                headers={"Authorization": f"Bearer {jwt}"},
                timeout=aiohttp.ClientTimeout(total=10)
            )
            
            if resp.status == 201 or resp.status == 200:
                result = await resp.json()
                ref_link = result.get("ref_link", "")
                ref_code = result.get("ref_code", "")
                
                await callback.message.edit_text(
                    f"🎉 <b>Вы стали партнёром AI Centers!</b>\n\n"
                    f"🔗 Ваша реферальная ссылка:\n<code>{ref_link}</code>\n\n"
                    f"📊 Комиссия: 20% (Bronze)\n"
                    f"📈 Рост: 5 продаж → 35%, 15 продаж → 50%\n\n"
                    f"Отправляйте ссылку клиентам. При каждой оплате — комиссия на ваш счёт!",
                    reply_markup=get_back_keyboard()
                )
            elif resp.status == 409:
                await callback.message.edit_text(
                    "✅ Вы уже партнёр! Ваша ссылка в личном кабинете:\naicenters.co/partners",
                    reply_markup=get_back_keyboard()
                )
            else:
                raise Exception(f"API {resp.status}")
                
    except Exception as e:
        logger.error(f"Partner registration failed: {e}")
        await callback.message.edit_text(
            "⚠️ Не удалось зарегистрироваться. Попробуйте позже или напишите @CARGORAPIDO",
            reply_markup=get_back_keyboard()
        )
    await callback.answer()


async def track_partner_referral(ref_code: str, user, plan_id: str, amount: int):
    """Track referral via Platform API."""
    try:
        async with aiohttp.ClientSession() as session:
            await session.post(
                f"{PLATFORM_API_URL}/partners/track",
                json={
                    "ref_code": ref_code,
                    "client_user_id": user.id,
                    "client_name": user.full_name,
                    "plan": plan_id,
                    "amount": amount
                },
                headers={"X-Admin-Key": os.getenv("ADMIN_API_KEY", "aicenters_admin_2026")},
                timeout=aiohttp.ClientTimeout(total=10)
            )
            logger.info(f"Referral tracked: ref={ref_code}, client={user.id}, plan={plan_id}")
    except Exception as e:
        logger.error(f"Referral tracking failed: {e}")


# ─── Register & Run ───
dp.include_router(router)

async def main():
    logger.info("Starting AI Centers Sales Bot v2.0...")
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not set!")
        return
    if BOT_TOKEN == "placeholder_token":
        logger.warning("BOT_TOKEN not set!")
    try:
        await dp.start_polling(bot, skip_updates=True)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
