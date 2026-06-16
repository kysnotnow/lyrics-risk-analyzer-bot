from typing import Self

from pydantic import BaseModel, Field, model_validator

from app.models.enums import RiskCategory, RiskLevel


class CategoryAssessment(BaseModel):
    category: RiskCategory
    level: RiskLevel
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str


class SuspiciousFragment(BaseModel):
    text: str
    category: RiskCategory
    level: RiskLevel
    confidence: float = Field(ge=0.0, le=1.0)
    literal_interpretation: str
    metaphorical_interpretation: str
    explanation: str


class ReplacementIdea(BaseModel):
    theme: str
    ideas: list[str] = Field(min_length=1)


class AnalysisResult(BaseModel):
    overall_risk: RiskLevel
    risk_score: float = Field(ge=0.0, le=1.0)
    categories: list[CategoryAssessment]
    suspicious_fragments: list[SuspiciousFragment]
    replacement_idea_cloud: list[ReplacementIdea]
    literal_interpretation: str
    metaphorical_interpretation: str
    explanation: str

    @model_validator(mode="after")
    def ensure_all_categories_present(self) -> Self:
        present = {item.category for item in self.categories}
        missing = set(RiskCategory) - present
        if missing:
            missing_labels = ", ".join(sorted(c.value for c in missing))
            raise ValueError(f"Missing category assessments: {missing_labels}")
        return self
