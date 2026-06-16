from dataclasses import dataclass
from datetime import datetime

from app.database.connection import Database


@dataclass(frozen=True, slots=True)
class StoredAnalysis:
    id: int
    user_id: int
    telegram_username: str | None
    lyrics: str
    result_json: str
    created_at: datetime


class AnalysisRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    async def save(
        self,
        user_id: int,
        telegram_username: str | None,
        lyrics: str,
        result_json: str,
    ) -> int:
        cursor = await self._database.connection.execute(
            """
            INSERT INTO analyses (user_id, telegram_username, lyrics, result_json)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, telegram_username, lyrics, result_json),
        )
        await self._database.connection.commit()
        return cursor.lastrowid or 0
