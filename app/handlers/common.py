from typing import Any

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router(name="common")


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    await message.answer(
        "<b>Lyrics Risk Analyzer</b>\n\n"
        "Send me song lyrics as a text message and I will analyze them for "
        "potentially risky content.\n\n"
        "<b>Categories:</b> drugs, drug glorification, crime, violence, "
        "sexual content, relationship content, extremism, self-harm.\n\n"
        "<b>Risk levels:</b> GREEN, YELLOW, RED.",
        parse_mode="HTML",
    )
