import asyncio
import logging
from typing import Any, Awaitable, Callable

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config.settings import get_settings
from app.handlers import common_router, lyrics_router
from app.logging_config import setup_logging
from app.services.container import ServiceContainer, build_container

logger = logging.getLogger(__name__)


class DependencyMiddleware:
    def __init__(self, container: ServiceContainer) -> None:
        self._container = container

    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        data["analysis_service"] = self._container.analysis_service
        data["report_formatter"] = self._container.report_formatter
        data["max_lyrics_length"] = self._container.settings.max_lyrics_length
        return await handler(event, data)


async def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)

    container = build_container(settings)
    await container.database.connect()

    logger.info(
        "LLM config: base_url=%s model=%s timeout=%ss",
        settings.llm_base_url,
        settings.llm_model,
        settings.llm_timeout_seconds,
    )
    await container.llm_service.verify_connection()

    bot = Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = Dispatcher()
    dispatcher.update.middleware(DependencyMiddleware(container))
    dispatcher.include_router(common_router)
    dispatcher.include_router(lyrics_router)

    logger.info("Starting bot polling")
    try:
        await dispatcher.start_polling(bot)
    finally:
        await container.database.close()
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
