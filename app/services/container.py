from dataclasses import dataclass

from app.config.settings import Settings
from app.database.connection import Database
from app.database.repository import AnalysisRepository
from app.services.analysis_service import AnalysisService
from app.services.llm_service import LLMService
from app.services.report_formatter import ReportFormatter


@dataclass(slots=True)
class ServiceContainer:
    settings: Settings
    database: Database
    repository: AnalysisRepository
    llm_service: LLMService
    analysis_service: AnalysisService
    report_formatter: ReportFormatter


def build_container(settings: Settings) -> ServiceContainer:
    database = Database(settings.database_path)
    repository = AnalysisRepository(database)
    llm_service = LLMService(settings)
    analysis_service = AnalysisService(llm_service, repository)
    report_formatter = ReportFormatter()
    return ServiceContainer(
        settings=settings,
        database=database,
        repository=repository,
        llm_service=llm_service,
        analysis_service=analysis_service,
        report_formatter=report_formatter,
    )
