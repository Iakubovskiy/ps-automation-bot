"""Bot entry point — initializes aiogram and registers dynamic dynamic_collector."""
import asyncio
import logging
import os
import sys
from pathlib import Path

# Ensure src/ is on Python path for Django + module imports
src_dir = str(Path(__file__).resolve().parent)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "framework.settings")
django.setup()

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from django.conf import settings

from modules.interface.bot_interface.handlers.dynamic_collector import router as collector_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Start the Telegram bot with the dynamic dynamic_collector handler."""
    bot_token = settings.BOT_TOKEN
    if not bot_token:
        logger.error("bot_token is not set in environment!")
        return

    bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    dp.include_router(collector_router)

    logger.info("Starting PIM bot…")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
