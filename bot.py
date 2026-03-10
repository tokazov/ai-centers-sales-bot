#!/usr/bin/env python3
"""
AI Centers — Sales Bot (@ai_centers_hub_bot)
Modular architecture: core.py + handlers/*.py

Modules:
  core.py           — Config, bot/dp instances, shared utilities
  handlers/payments.py    — Stars invoices, bank, payment callbacks
  handlers/funnel.py      — Sales funnel (step1, biz/leads/demo/pricing)
  handlers/computer_use.py — Computer Use pilot, questionnaire, activation
  handlers/commands.py    — /start, /menu, /reset + menu callbacks
  handlers/messages.py    — on_text (main router), on_voice, STT
  handlers/onboarding.py  — Bot creation: channel, data, create
  handlers/channels.py    — Channel guides (Telegram/WA/IG/Web)
  handlers/management.py  — Bot management (train/edit/billing/FAQ)
"""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Core: bot, dp, config, utilities
from core import bot, dp

# Handler modules — each exports a `router`
from handlers.payments import router as payments_router
from handlers.funnel import router as funnel_router
from handlers.computer_use import router as cu_router
from handlers.commands import router as commands_router
from handlers.messages import router as messages_router
from handlers.onboarding import router as onboarding_router
from handlers.channels import router as channels_router
from handlers.management import router as management_router

# Register routers (ORDER MATTERS for callback/message priority)
# 1. Payments first (pre_checkout_query, successful_payment)
dp.include_router(payments_router)
# 2. Commands (/start, /menu, /reset)
dp.include_router(commands_router)
# 3. Computer Use funnel callbacks
dp.include_router(cu_router)
# 4. Sales funnel callbacks
dp.include_router(funnel_router)
# 5. Onboarding callbacks (ob_channel, ob_create_bot)
dp.include_router(onboarding_router)
# 6. Channel guide callbacks
dp.include_router(channels_router)
# 7. Management callbacks
dp.include_router(management_router)
# 8. Messages LAST (catch-all text/voice handlers)
dp.include_router(messages_router)


async def main():
    logger.info("AI Centers Sales Bot (modular) starting...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
