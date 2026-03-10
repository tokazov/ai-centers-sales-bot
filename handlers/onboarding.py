"""Bot creation onboarding: channel select, data collection, create bot."""

import logging
from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core import bot, ADMIN_ID, get_session, detect_lang, t

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(F.data.startswith("ob_channel_"))
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
    except Exception: pass
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

