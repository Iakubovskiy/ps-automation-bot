"""Main entry point for the Telegram bot."""
import asyncio
import logging
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer

try:
    from src.config import settings
    from src.handlers.collector import router as collector_router
except ModuleNotFoundError:
    project_root = Path(__file__).resolve().parents[1]
    sys.path.append(str(project_root))
    from src.config import settings
    from src.handlers.collector import router as collector_router

async def main() -> None:
    """Initialize and start the bot."""
    session = AiohttpSession(
        api=TelegramAPIServer.from_base("http://telegram-bot-api:8081", is_local=True),
    )

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout
    )

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        session=session,
    )
    dp = Dispatcher()
    dp.include_router(collector_router)

    logging.info("Starting bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
