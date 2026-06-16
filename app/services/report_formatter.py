from app.models.analysis import AnalysisResult
from app.models.enums import RiskCategory, RiskLevel

RISK_EMOJI = {
    RiskLevel.GREEN: "🟢",
    RiskLevel.YELLOW: "🟡",
    RiskLevel.RED: "🔴",
}

CATEGORY_LABELS = {
    RiskCategory.DRUGS: "Drugs",
    RiskCategory.DRUG_GLORIFICATION: "Drug glorification",
    RiskCategory.CRIME: "Crime",
    RiskCategory.VIOLENCE: "Violence",
    RiskCategory.SEXUAL_CONTENT: "Sexual content",
    RiskCategory.RELATIONSHIP_CONTENT: "Relationship content",
    RiskCategory.EXTREMISM: "Extremism",
    RiskCategory.SELF_HARM: "Self-harm",
}


class ReportFormatter:
    def format(self, result: AnalysisResult) -> str:
        sections = [
            self._format_header(result),
            self._format_summary(result),
            self._format_categories(result),
            self._format_fragments(result),
            self._format_replacements(result),
        ]
        return "\n\n".join(section for section in sections if section)

    def _format_header(self, result: AnalysisResult) -> str:
        emoji = RISK_EMOJI[result.overall_risk]
        score_pct = int(result.risk_score * 100)
        return (
            f"<b>Lyrics Risk Report</b>\n"
            f"{emoji} Overall risk: <b>{result.overall_risk.value}</b>\n"
            f"Risk score: <b>{score_pct}%</b>"
        )

    def _format_summary(self, result: AnalysisResult) -> str:
        return (
            "<b>Summary</b>\n"
            f"{self._escape(result.explanation)}\n\n"
            f"<b>Literal meaning</b>\n{self._escape(result.literal_interpretation)}\n\n"
            f"<b>Metaphorical meaning</b>\n"
            f"{self._escape(result.metaphorical_interpretation)}"
        )

    def _format_categories(self, result: AnalysisResult) -> str:
        lines = ["<b>Category breakdown</b>"]
        for item in sorted(result.categories, key=lambda c: c.category.value):
            emoji = RISK_EMOJI[item.level]
            label = CATEGORY_LABELS[item.category]
            confidence = int(item.confidence * 100)
            lines.append(
                f"{emoji} <b>{label}</b> — {item.level.value} "
                f"({confidence}% conf.)\n{self._escape(item.explanation)}"
            )
        return "\n".join(lines)

    def _format_fragments(self, result: AnalysisResult) -> str:
        if not result.suspicious_fragments:
            return ""
        lines = ["<b>Suspicious fragments</b>"]
        for index, fragment in enumerate(result.suspicious_fragments, start=1):
            emoji = RISK_EMOJI[fragment.level]
            label = CATEGORY_LABELS[fragment.category]
            confidence = int(fragment.confidence * 100)
            lines.append(
                f"{index}. {emoji} <i>\"{self._escape(fragment.text)}\"</i>\n"
                f"   {label} — {fragment.level.value} ({confidence}% conf.)\n"
                f"   Literal: {self._escape(fragment.literal_interpretation)}\n"
                f"   Metaphorical: {self._escape(fragment.metaphorical_interpretation)}\n"
                f"   Note: {self._escape(fragment.explanation)}"
            )
        return "\n".join(lines)

    def _format_replacements(self, result: AnalysisResult) -> str:
        if not result.replacement_idea_cloud:
            return ""
        lines = ["<b>Replacement idea cloud</b>"]
        for cloud in result.replacement_idea_cloud:
            ideas = ", ".join(self._escape(idea) for idea in cloud.ideas)
            lines.append(f"• <b>{self._escape(cloud.theme)}</b>: {ideas}")
        return "\n".join(lines)

    @staticmethod
    def _escape(text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
