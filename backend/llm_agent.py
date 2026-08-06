"""
LLM Agent for fact-checking using Groq API with structured output parsing.

Uses a carefully engineered system prompt to produce a structured report
with sections for Verdict, Confidence, Summary, Explanation, Supporting /
Contradicting evidence, Professional Fact Checks, Latest News, and Sources.
"""

import os
import re
import logging
from typing import Optional

from groq import Groq

from backend.utils import SearchResult, FactCheckReport

logger = logging.getLogger("fact_checker.llm")


class FactCheckerAgent:
    """Evaluates claims against retrieved evidence using Groq LLM."""

    SYSTEM_PROMPT: str = """\
You are an expert AI fact-checker. Analyze the claim STRICTLY using ONLY the
provided evidence. Follow these rules without exception:

1. Base every conclusion on the evidence supplied. NEVER use outside knowledge.
2. If the evidence is insufficient, your verdict MUST be UNVERIFIABLE.
3. Remain objective and unbiased. Weigh all perspectives in the evidence.
4. Cite specific sources (by title and URL) to justify your analysis.
5. NEVER fabricate, hallucinate, or infer facts beyond the evidence.

Respond in EXACTLY this format — use the exact section markers shown:

[VERDICT]
One of: TRUE | FALSE | MIXED | MISLEADING | UNVERIFIABLE

[CONFIDENCE]
A single integer from 0 to 100 (represents percentage confidence)

[SUMMARY]
2-3 sentence summary of your finding.

[DETAILED_EXPLANATION]
Thorough, step-by-step analysis using bullet points.

[SUPPORTING_EVIDENCE]
Evidence that supports the claim. Cite sources by title and URL.
If none, write: "No supporting evidence found."

[CONTRADICTING_EVIDENCE]
Evidence that contradicts the claim. Cite sources by title and URL.
If none, write: "No contradicting evidence found."

[PROFESSIONAL_FACT_CHECKS]
Summarise any professional fact-check ratings found (e.g. from PolitiFact,
Snopes, FactCheck.org, Full Fact). If none, write: "No professional fact
checks found for this claim."

[LATEST_NEWS]
Summarise the most recent news coverage related to this claim.
If none, write: "No recent news coverage found."

[SOURCES]
List every source used, one per line:
- Source Title — URL

VERDICT GUIDELINES:
• TRUE — Strong, consistent evidence confirms the claim.
• FALSE — Strong, consistent evidence refutes the claim.
• MIXED — Evidence both supports and contradicts parts of the claim.
• MISLEADING — The claim contains some truth but is presented deceptively.
• UNVERIFIABLE — Insufficient or conflicting evidence to decide.\
"""

    # Ordered section markers used for parsing
    _SECTION_KEYS: list[str] = [
        "VERDICT",
        "CONFIDENCE",
        "SUMMARY",
        "DETAILED_EXPLANATION",
        "SUPPORTING_EVIDENCE",
        "CONTRADICTING_EVIDENCE",
        "PROFESSIONAL_FACT_CHECKS",
        "LATEST_NEWS",
        "SOURCES",
    ]

    _SECTION_FIELD_MAP: dict[str, str] = {
        "VERDICT": "verdict",
        "CONFIDENCE": "confidence",
        "SUMMARY": "summary",
        "DETAILED_EXPLANATION": "detailed_explanation",
        "SUPPORTING_EVIDENCE": "supporting_evidence",
        "CONTRADICTING_EVIDENCE": "contradicting_evidence",
        "PROFESSIONAL_FACT_CHECKS": "professional_fact_checks",
        "LATEST_NEWS": "latest_news_summary",
        "SOURCES": "sources",
    }

    VALID_VERDICTS: set[str] = {
        "TRUE", "FALSE", "MIXED", "MISLEADING", "UNVERIFIABLE",
    }

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key: str = api_key or os.environ.get("GROQ_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY is missing. Provide it via .env or the sidebar."
            )
        self.client = Groq(api_key=self.api_key)
        self.model: str = "llama-3.3-70b-versatile"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate_claim(
        self,
        claim: str,
        evidence: list[SearchResult],
    ) -> FactCheckReport:
        """Send claim + evidence to Groq and return a parsed FactCheckReport."""
        from backend.search_engine import format_context_for_llm

        context = format_context_for_llm(evidence)
        user_prompt = (
            f'CLAIM TO VERIFY:\n"{claim}"\n\n'
            f"RETRIEVED EVIDENCE:\n{context}\n\n"
            "Analyze the claim using ONLY the evidence above. "
            "Respond in the exact structured format specified."
        )

        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                model=self.model,
                temperature=0.0,
                max_tokens=4096,
            )
            raw: str = response.choices[0].message.content
            logger.info("LLM response received (%d chars)", len(raw))
            return self._parse_response(raw)

        except Exception as exc:
            logger.error("LLM evaluation failed: %s", exc)
            return FactCheckReport(
                verdict="UNVERIFIABLE",
                confidence=0,
                summary=f"Error during LLM evaluation: {exc}",
                raw_response=str(exc),
            )

    # ------------------------------------------------------------------
    # Response Parser
    # ------------------------------------------------------------------

    def _parse_response(self, raw: str) -> FactCheckReport:
        """Parse the structured LLM response into a :class:`FactCheckReport`."""
        report = FactCheckReport(raw_response=raw)

        keys = self._SECTION_KEYS
        for idx, key in enumerate(keys):
            start_pat = rf"\[{key}\]\s*\n?"
            end_pat = rf"\[{keys[idx + 1]}\]" if idx + 1 < len(keys) else r"\Z"

            match = re.search(start_pat + r"(.*?)" + end_pat, raw, re.DOTALL)
            if not match:
                continue

            value = match.group(1).strip()
            field = self._SECTION_FIELD_MAP[key]

            if field == "verdict":
                report.verdict = self._normalize_verdict(value)
            elif field == "confidence":
                num = re.search(r"(\d+)", value)
                report.confidence = min(100, max(0, int(num.group(1)))) if num else 0
            else:
                setattr(report, field, value)

        # Fallback when section parsing fails entirely
        if not report.summary and raw:
            report.summary = "See the detailed analysis below."
            report.detailed_explanation = raw

        return report

    @classmethod
    def _normalize_verdict(cls, text: str) -> str:
        """Extract a valid verdict keyword from *text*."""
        upper = text.upper().strip()
        for v in cls.VALID_VERDICTS:
            if v in upper:
                return v
        return "UNVERIFIABLE"
