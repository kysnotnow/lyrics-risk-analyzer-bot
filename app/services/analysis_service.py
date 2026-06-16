import logging

from app.database.repository import AnalysisRepository
from app.models.analysis import AnalysisResult
from app.services.llm_service import LLMService, LLMServiceError

logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(
        self,
        llm_service: LLMService,
        repository: AnalysisRepository,
    ) -> None:
        self._llm_service = llm_service
        self._repository = repository

    async def analyze(
        self,
        lyrics: str,
        user_id: int,
        telegram_username: str | None,
    ) -> AnalysisResult:
        logger.info("Starting analysis for user_id=%s", user_id)
        try:
            result = await self._llm_service.analyze_lyrics(lyrics)
        except LLMServiceError:
            raise

        await self._repository.save(
            user_id=user_id,
            telegram_username=telegram_username,
            lyrics=lyrics,
            result_json=result.model_dump_json(),
        )
        logger.info(
            "Analysis complete for user_id=%s overall_risk=%s score=%.2f",
            user_id,
            result.overall_risk.value,
            result.risk_score,
        )
        return result
