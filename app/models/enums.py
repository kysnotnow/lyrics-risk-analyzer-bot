from enum import StrEnum


class RiskLevel(StrEnum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"


class RiskCategory(StrEnum):
    DRUGS = "drugs"
    DRUG_GLORIFICATION = "drug_glorification"
    CRIME = "crime"
    VIOLENCE = "violence"
    SEXUAL_CONTENT = "sexual_content"
    RELATIONSHIP_CONTENT = "relationship_content"
    EXTREMISM = "extremism"
    SELF_HARM = "self_harm"
