import re
from collections import Counter

from app.enricher.base import Enricher, Enrichment

SUMMARY_SENTENCES = 2
SUMMARY_MAX_CHARS = 300
KEYWORD_COUNT = 5

# category -> words that hint at it; most hits wins
CATEGORY_HINTS = {
    "invoice": ["invoice", "amount due", "payment", "vat", "total", "bill to"],
    "contract": ["agreement", "parties", "party", "terms", "hereby", "contract", "obligations"],
    "report": ["report", "analysis", "results", "quarter", "revenue", "findings"],
    "cv": ["experience", "education", "skills", "resume", "curriculum vitae"],
    "letter": ["dear", "sincerely", "regards", "yours"],
}

STOPWORDS = set(
    """a an and are as at be been but by can could did do does for from had has have he her his i if in
    into is it its may more most no not of on or our she so than that the their them then there these
    they this to was we were what when which who will with would you your also all any each per page""".split()
)


class MockLlmEnricher(Enricher):
    """Stand-in for an LLM call (brief allows mocking paid APIs). Simple heuristics, deterministic."""

    def enrich(self, text: str) -> Enrichment:
        text = " ".join(text.split())  # collapse whitespace / newlines
        if not text:
            return Enrichment(summary="No text content found.", category="other")
        return Enrichment(
            summary=_summary(text),
            category=_category(text.lower()),
            keywords=_keywords(text.lower()),
        )


def _summary(text: str) -> str:
    # first sentences, capped
    sentences = re.split(r"(?<=[.!?])\s+", text)
    summary = " ".join(sentences[:SUMMARY_SENTENCES])
    return summary if len(summary) <= SUMMARY_MAX_CHARS else summary[:SUMMARY_MAX_CHARS].rstrip() + "…"


def _keywords(text: str) -> list[str]:
    # most frequent meaningful words (ties keep first-seen order)
    words = [w for w in re.findall(r"[a-z][a-z-]{2,}", text) if w not in STOPWORDS]
    return [w for w, _ in Counter(words).most_common(KEYWORD_COUNT)]


def _category(text: str) -> str:
    scores = {cat: sum(text.count(hint) for hint in hints) for cat, hints in CATEGORY_HINTS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "other"
