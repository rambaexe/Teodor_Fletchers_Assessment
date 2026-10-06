from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Enrichment:
    summary: str
    category: str  # invoice | contract | report | cv | letter | other
    keywords: list[str] = field(default_factory=list)


class Enricher(ABC):
    """Text -> summary / category / keywords. Mock now; an LLM call (e.g. Claude) later."""

    @abstractmethod
    def enrich(self, text: str) -> Enrichment: ...
