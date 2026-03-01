#!/usr/bin/env python3
"""
AI Centers Sales Bot
Telegram бот для продажи AI-ассистентов
"""

import os
import json
import logging
import asyncio
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
import google.generativeai as genai

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN", "placeholder_token")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "5309206282"))

# Путь к файлу лидов
LEADS_FILE = "leads.json"

# Инициализация Gemini
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')

# System prompt для AI-чата
SALES_PROMPT = """Ты продажник AI Centers. Продаёшь AI-ассистентов для бизнеса. 
Цены: от $15/мес. Преимущества: работает 24/7, отвечает на 6 языках, настройка за 24 часа, 
дешевле сотрудника в 50 раз. Будь убедительным но не навязчивым. 
Всегда веди к покупке или демо. Определи язык клиента и отвечай на нём."""

# FSM для сбора заявки
class ContactForm(StatesGroup):
    waiting_for_name = State()
    waiting_for_business = State()
    waiting_for_niche = State()
    waiting_for_contact = State()

# FSM для онбординга после оплаты
class Onboarding(StatesGroup):
    waiting_for_business_name = State()
    waiting_for_niche = State()
    waiting_for_description = State()

# Тарифы
PLANS = {
    "starter": {
        "name": "Starter",
        "price": "$15/мес",
        "stars": 150,
        "features": [
            "✓ Telegram бот",
            "✓ 1 ниша",
            "✓ 500 сообщений/мес",
            "✓ Базовая поддержка"
        ]
    },
    "business": {
        "name": "Business",
        "price": "$49/мес",
        "stars": 500,
        "badge": "⭐ Популярный",
        "features": [
            "✓ Telegram + виджет сайта",
            "✓ Любая ниша",
            "✓ 3000 сообщений/мес",
            "✓ Аналитика",
            "✓ Приоритетная поддержка"
        ]
    },
    "pro": {
        "name": "Pro",
        "price": "$99/мес",
        "stars": 1000,
        "features": [
            "✓ Всё из Business",
            "✓ Безлимит сообщений",
            "✓ WhatsApp интеграция",
            "✓ Кастомизация промпта",
            "✓ Персональный менеджер"
        ]
    },
    "enterprise": {
        "name": "Enterprise",
        "price": "$149/мес",
        "stars": 1500,
        "features": [
            "✓ Всё из Pro",
            "✓ Голосовой AI-секретарь",
            "✓ CRM интеграция",
            "✓ API доступ",
            "✓ SLA 99.9%"
        ]
    }
}

# Ниши
NICHES = [
    ("restaurant", "🍽 Ресторан"),
    ("salon", "💇 Салон"),
    ("delivery", "🚚 Доставка"),
    ("hotel", "🏨 Отель"),
    ("fitness", "💪 Фитнес"),
    ("clinic", "⚕️ Клиника"),
    ("other", "📝 Другое")
]

FAQ_ANSWERS = {
    "how_it_works": """🔧 **Как это работает?**

1. Вы выбираете тариф и оплачиваете
2. Заполняете информацию о бизнесе (5 минут)
3. Наш AI обучается на вашей нише (автоматически)
4. Через 24 часа получаете готового бота
5. Интегрируете в Telegram/сайт одной ссылкой

Бот отвечает клиентам 24/7, записывает на услуги, консультирует и передаёт заявки вам.""",
    
    "pricing": """💰 **Сколько стоит?**

📦 **Starter** — $15/мес  
Идеально для старта

📦 **Business** — $49/мес ⭐  
Самый популярный! Для активного бизнеса

📦 **Pro** — $99/мес  
Для масштаба + WhatsApp

📦 **Enterprise** — $149/мес  
Полный комплект + голосовой AI

Все тарифы — без скрытых комиссий. Настройка включена.""",
    
    "speed": """⚡ **Как быстро запустите?**

✅ **24 часа** с момента оплаты!

Процесс:
• 0 часов — оплатили и заполнили данные
• 2 часа — AI обучен на вашей нише
• 12 часов — бот протестирован
• 24 часа — передаём вам готовое решение

Поддержка 24/7 даже на минимальном тарифе.""",
    
    "niches": """🎯 **Какие ниши поддерживаете?**

Топ-ниши (готовые шаблоны):
• Рестораны и кафе
• Салоны красоты и барбершопы
• Доставка еды/товаров
• Отели и хостелы
• Фитнес-клубы
• Медицинские клиники

Но мы настраиваем под **любой бизнес**:
Автосервисы, юристы, агентства недвижимости, школы, магазины — всё что угодно!

AI учится на вашем описании за пару часов.""",
    
    "trial": """🎁 **Можно попробовать бесплатно?**

Да! У нас есть **демо-бот**:
👉 @aicenters_demo_bot

Там вы можете:
✓ Выбрать нишу (ресторан, салон, отель...)
✓ Пообщаться как клиент
✓ Увидеть, как AI ведёт диалог

Это реальный AI — такой же получите вы, только под свой бизнес.

Попробуйте прямо сейчас! 🚀"""
}


# Инициализация бота
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()


# Функции для работы с лидами
def save_lead(lead_data: dict):
    """Сохранение лида в JSON файл"""
    leads = []
    if os.path.exists(LEADS_FILE):
        with open(LEADS_FILE, 'r', encoding='utf-8') as f:
            try:
                leads = json.load(f)
            except json.JSONDecodeError:
                leads = []
    
    lead_data['timestamp'] = datetime.now().isoformat()
    leads.append(lead_data)
    
    with open(LEADS_FILE, 'w', encoding='utf-8') as f:
        json.dump(leads, f, ensure_ascii=False, indent=2)


# Клавиатуры
def get_main_menu():
    """Главное меню"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Демо", callback_data="demo")],
        [InlineKeyboardButton(text="💰 Тарифы", callback_data="pricing")],
        [InlineKeyboardButton(text="📞 Связаться", callback_data="contact")],
        [InlineKeyboardButton(text="❓ FAQ", callback_data="faq")]
    ])
    return keyboard


def get_pricing_keyboard():
    """Клавиатура с тарифами"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подключить Starter", callback_data="buy_starter")],
        [InlineKeyboardButton(text="Подключить Business ⭐", callback_data="buy_business")],
        [InlineKeyboardButton(text="Подключить Pro", callback_data="buy_pro")],
        [InlineKeyboardButton(text="Подключить Enterprise", callback_data="buy_enterprise")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
    ])
    return keyboard


def get_niche_keyboard():
    """Клавиатура с нишами"""
    buttons = [[InlineKeyboardButton(text=name, callback_data=f"niche_{code}")] 
               for code, name in NICHES]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def get_faq_keyboard():
    """Клавиатура FAQ"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Как это работает?", callback_data="faq_how_it_works")],
        [InlineKeyboardButton(text="Сколько стоит?", callback_data="faq_pricing")],
        [InlineKeyboardButton(text="Как быстро запустите?", callback_data="faq_speed")],
        [InlineKeyboardButton(text="Какие ниши поддерживаете?", callback_data="faq_niches")],
        [InlineKeyboardButton(text="Можно попробовать бесплатно?", callback_data="faq_trial")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
    ])
    return keyboard


def get_back_keyboard():
    """Кнопка назад"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_to_menu")]
    ])
    return keyboard


# Обработчики команд
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработка команды /start"""
    await state.clear()
    
    welcome_text = """👋 **Привет! Я AI Centers** — мы создаём умных AI-ассистентов для бизнеса за 24 часа.

Что вас интересует?"""
    
    await message.answer(welcome_text, reply_markup=get_main_menu())


# Обработчики callback
@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    
    welcome_text = """👋 **Привет! Я AI Centers** — мы создаём умных AI-ассистентов для бизнеса за 24 часа.

Что вас интересует?"""
    
    await callback.message.edit_text(welcome_text, reply_markup=get_main_menu())
    await callback.answer()


@router.callback_query(F.data == "demo")
async def show_demo(callback: CallbackQuery):
    """Показ демо"""
    demo_text = """🎯 **Попробуйте нашего демо-бота!**

Выберите нишу и пообщайтесь как клиент:
👉 @aicenters_demo_bot

Это реальный AI — такой же получите вы, только настроенный под ваш бизнес!"""
    
    await callback.message.edit_text(demo_text, reply_markup=get_back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "pricing")
async def show_pricing(callback: CallbackQuery):
    """Показ тарифов"""
    pricing_text = "💰 **Выберите тариф:**\n\n"
    
    for plan_id, plan in PLANS.items():
        pricing_text += f"━━━━━━━━━━━━━━━\n"
        pricing_text += f"📦 **{plan['name']}**\n"
        pricing_text += f"💵 **{plan['price']}**"
        if "badge" in plan:
            pricing_text += f" {plan['badge']}"
        pricing_text += "\n\n"
        pricing_text += "\n".join(plan['features'])
        pricing_text += "\n\n"
    pricing_text += "━━━━━━━━━━━━━━━"
    
    await callback.message.edit_text(pricing_text, reply_markup=get_pricing_keyboard())
    await callback.answer()


@router.callback_query(F.data == "contact")
async def start_contact_form(callback: CallbackQuery, state: FSMContext):
    """Начало формы связи"""
    await callback.message.edit_text("📝 Отлично! Давайте познакомимся.\n\n**Как вас зовут?**")
    await state.set_state(ContactForm.waiting_for_name)
    await callback.answer()


@router.callback_query(F.data == "faq")
async def show_faq(callback: CallbackQuery):
    """Показ FAQ"""
    faq_text = "❓ **Часто задаваемые вопросы:**\n\nВыберите интересующий вопрос:"
    await callback.message.edit_text(faq_text, reply_markup=get_faq_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("faq_"))
async def show_faq_answer(callback: CallbackQuery):
    """Показ ответа на вопрос FAQ"""
    question_id = callback.data.replace("faq_", "")
    answer = FAQ_ANSWERS.get(question_id, "Ответ не найден")
    
    await callback.message.edit_text(answer, reply_markup=get_back_keyboard())
    await callback.answer()


# Обработка формы связи
@router.message(StateFilter(ContactForm.waiting_for_name))
async def process_name(message: Message, state: FSMContext):
    """Обработка имени"""
    await state.update_data(name=message.text)
    await message.answer("Отлично! **Как называется ваш бизнес?**")
    await state.set_state(ContactForm.waiting_for_business)


@router.message(StateFilter(ContactForm.waiting_for_business))
async def process_business(message: Message, state: FSMContext):
    """Обработка названия бизнеса"""
    await state.update_data(business=message.text)
    await message.answer("**В какой нише вы работаете?**", reply_markup=get_niche_keyboard())
    await state.set_state(ContactForm.waiting_for_niche)


@router.callback_query(StateFilter(ContactForm.waiting_for_niche), F.data.startswith("niche_"))
async def process_niche(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора ниши"""
    niche_code = callback.data.replace("niche_", "")
    niche_name = next((name for code, name in NICHES if code == niche_code), "Неизвестно")
    
    await state.update_data(niche=niche_name)
    await callback.message.edit_text("**Как с вами связаться?**\n\nНапишите номер телефона или Telegram-аккаунт:")
    await state.set_state(ContactForm.waiting_for_contact)
    await callback.answer()


@router.message(StateFilter(ContactForm.waiting_for_contact))
async def process_contact(message: Message, state: FSMContext):
    """Обработка контакта и сохранение заявки"""
    data = await state.get_data()
    data['contact'] = message.text
    data['user_id'] = message.from_user.id
    data['username'] = message.from_user.username
    
    # Сохранение лида
    save_lead(data)
    
    # Уведомление админа
    admin_message = f"""🆕 **Новая заявка!**

👤 Имя: {data['name']}
🏢 Бизнес: {data['business']}
🎯 Ниша: {data['niche']}
📞 Контакт: {data['contact']}
🆔 User ID: {data['user_id']}
👤 Username: @{data['username'] or 'не указан'}"""
    
    try:
        await bot.send_message(ADMIN_CHAT_ID, admin_message)
    except Exception as e:
        logger.error(f"Не удалось отправить уведомление админу: {e}")
    
    # Ответ пользователю
    await message.answer(
        f"""✅ **Спасибо, {data['name']}!**

Ваша заявка принята. Мы свяжемся с вами в ближайшее время по контакту: {data['contact']}

А пока можете посмотреть наши тарифы или попробовать демо-бота! 🚀""",
        reply_markup=get_main_menu()
    )
    
    await state.clear()


# Обработка оплаты
@router.callback_query(F.data.startswith("buy_"))
async def process_payment(callback: CallbackQuery):
    """Создание invoice для оплаты"""
    plan_id = callback.data.replace("buy_", "")
    plan = PLANS.get(plan_id)
    
    if not plan:
        await callback.answer("❌ Тариф не найден", show_alert=True)
        return
    
    # Создание invoice
    prices = [LabeledPrice(label=f"Тариф {plan['name']}", amount=plan['stars'])]
    
    description = f"{plan['name']} — {plan['price']}\n" + "\n".join(plan['features'])
    
    try:
        await bot.send_invoice(
            chat_id=callback.message.chat.id,
            title=f"AI Centers — {plan['name']}",
            description=description,
            payload=f"plan_{plan_id}",
            provider_token="",  # Для Telegram Stars токен не нужен
            currency="XTR",  # Telegram Stars
            prices=prices
        )
        await callback.answer("✨ Создан счёт на оплату")
    except Exception as e:
        logger.error(f"Ошибка создания invoice: {e}")
        await callback.answer("❌ Ошибка создания счёта. Попробуйте позже.", show_alert=True)


@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    """Подтверждение платежа"""
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(message: Message, state: FSMContext):
    """Обработка успешной оплаты"""
    payment = message.successful_payment
    plan_id = payment.invoice_payload.replace("plan_", "")
    plan = PLANS.get(plan_id)
    
    # Благодарность
    success_text = f"""🎉 **Спасибо за покупку!**

Вы подключили тариф **{plan['name']}**.

Сейчас запустим процесс настройки вашего AI-ассистента.

**Название вашего бизнеса?**"""
    
    await message.answer(success_text)
    
    # Начало онбординга
    await state.update_data(plan=plan_id)
    await state.set_state(Onboarding.waiting_for_business_name)
    
    # Уведомление админа
    admin_message = f"""💰 **Новая оплата!**

💳 Тариф: {plan['name']}
⭐️ Сумма: {plan['stars']} Stars
👤 User: {message.from_user.full_name}
🆔 User ID: {message.from_user.id}
👤 Username: @{message.from_user.username or 'не указан'}"""
    
    try:
        await bot.send_message(ADMIN_CHAT_ID, admin_message)
    except Exception as e:
        logger.error(f"Не удалось отправить уведомление админу: {e}")


# Онбординг после оплаты
@router.message(StateFilter(Onboarding.waiting_for_business_name))
async def onboarding_business(message: Message, state: FSMContext):
    """Сбор названия бизнеса"""
    await state.update_data(business_name=message.text)
    await message.answer("**В какой нише вы работаете?**", reply_markup=get_niche_keyboard())
    await state.set_state(Onboarding.waiting_for_niche)


@router.callback_query(StateFilter(Onboarding.waiting_for_niche), F.data.startswith("niche_"))
async def onboarding_niche(callback: CallbackQuery, state: FSMContext):
    """Сбор ниши"""
    niche_code = callback.data.replace("niche_", "")
    niche_name = next((name for code, name in NICHES if code == niche_code), "Неизвестно")
    
    await state.update_data(niche=niche_name)
    await callback.message.edit_text(
        "**Расскажите о вашем бизнесе:**\n\n"
        "Опишите в 2-3 предложениях:\n"
        "• Что вы предлагаете\n"
        "• Ваши услуги\n"
        "• Что важно знать клиентам"
    )
    await state.set_state(Onboarding.waiting_for_description)
    await callback.answer()


@router.message(StateFilter(Onboarding.waiting_for_description))
async def onboarding_complete(message: Message, state: FSMContext):
    """Завершение онбординга"""
    data = await state.get_data()
    data['description'] = message.text
    data['user_id'] = message.from_user.id
    data['username'] = message.from_user.username
    data['timestamp'] = datetime.now().isoformat()
    
    # Сохранение данных онбординга
    onboarding_file = "onboarding.json"
    onboardings = []
    if os.path.exists(onboarding_file):
        with open(onboarding_file, 'r', encoding='utf-8') as f:
            try:
                onboardings = json.load(f)
            except json.JSONDecodeError:
                onboardings = []
    
    onboardings.append(data)
    
    with open(onboarding_file, 'w', encoding='utf-8') as f:
        json.dump(onboardings, f, ensure_ascii=False, indent=2)
    
    # Уведомление админа о завершении онбординга
    admin_message = f"""✅ **Онбординг завершён!**

👤 User: {message.from_user.full_name}
🆔 User ID: {data['user_id']}
📦 Тариф: {PLANS[data['plan']]['name']}
🏢 Бизнес: {data['business_name']}
🎯 Ниша: {data['niche']}
📝 Описание: {data['description']}"""
    
    try:
        await bot.send_message(ADMIN_CHAT_ID, admin_message)
    except Exception as e:
        logger.error(f"Не удалось отправить уведомление админу: {e}")
    
    # Финальное сообщение пользователю
    await message.answer(
        f"""✅ **Отлично! Всё готово для запуска.**

🏢 Бизнес: {data['business_name']}
🎯 Ниша: {data['niche']}

⏱ **Через 24 часа** ваш AI-ассистент будет готов!

Мы настроим его на основе ваших данных и пришлём инструкцию по подключению.

📞 Если появятся вопросы — пишите прямо сюда, я на связи 24/7!""",
        reply_markup=get_main_menu()
    )
    
    await state.clear()


# AI-чат через Gemini
@router.message()
async def ai_chat(message: Message):
    """Общий AI-чат через Gemini"""
    user_message = message.text
    
    try:
        # Отправка "печатает..."
        await bot.send_chat_action(message.chat.id, "typing")
        
        # Запрос к Gemini
        chat = gemini_model.start_chat(history=[])
        response = await asyncio.to_thread(
            chat.send_message,
            f"{SALES_PROMPT}\n\nКлиент: {user_message}"
        )
        
        await message.answer(response.text, reply_markup=get_main_menu())
        
    except Exception as e:
        logger.error(f"Ошибка при обращении к Gemini: {e}")
        await message.answer(
            "Извините, произошла ошибка. Попробуйте снова или выберите действие из меню:",
            reply_markup=get_main_menu()
        )


# Регистрация роутера
dp.include_router(router)


# Запуск бота
async def main():
    """Главная функция запуска"""
    logger.info("Запуск AI Centers Sales Bot...")
    
    # Проверка переменных окружения
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY не установлен!")
        return
    
    if BOT_TOKEN == "placeholder_token":
        logger.warning("BOT_TOKEN не установлен, используется placeholder!")
    
    try:
        await dp.start_polling(bot, skip_updates=True)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
