from aiogram import F, Router
from aiogram.types import Message

from app.services.analysis_service import AnalysisService
from app.services.llm_service import LLMServiceError
from app.services.report_formatter import ReportFormatter

router = Router(name="lyrics")

TELEGRAM_MESSAGE_LIMIT = 4096


def _split_message(text: str, limit: int = TELEGRAM_MESSAGE_LIMIT) -> list[str]:
    if len(text) <= limit:
        return [text]
    chunks: list[str] = []
    current = ""
    for line in text.split("\n"):
        candidate = f"{current}\n{line}" if current else line
        if len(candidate) <= limit:
            current = candidate
            continue
        if current:
            chunks.append(current)
        while len(line) > limit:
            chunks.append(line[:limit])
            line = line[limit:]
        current = line
    if current:
        chunks.append(current)
    return chunks


@router.message(F.text)
async def handle_lyrics(
    message: Message,
    analysis_service: AnalysisService,
    report_formatter: ReportFormatter,
    max_lyrics_length: int,
) -> None:
    if message.text is None or message.from_user is None:
        return

    lyrics = message.text.strip()
    if not lyrics:
        await message.answer("Please send non-empty lyrics text.")
        return

    if lyrics.startswith("/"):
        return

    if len(lyrics) > max_lyrics_length:
        await message.answer(
            f"Lyrics are too long. Maximum length is {max_lyrics_length} characters."
        )
        return

    status_message = await message.answer("Analyzing lyrics, please wait…")

    try:
        result = await analysis_service.analyze(
            lyrics=lyrics,
            user_id=message.from_user.id,
            telegram_username=message.from_user.username,
        )
    except LLMServiceError:
        await status_message.edit_text(
            "Analysis failed. Please try again in a moment."
        )
        return

    report = report_formatter.format(result)
    chunks = _split_message(report)

    await status_message.edit_text(chunks[0], parse_mode="HTML")
    for chunk in chunks[1:]:
        await message.answer(chunk, parse_mode="HTML")
