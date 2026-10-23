from __future__ import annotations

from dataclasses import asdict, dataclass

from .model import HybridModel
from .text import normalize_text


@dataclass(frozen=True)
class PassageMatch:
    suspicious: str
    source: str
    score: float


def find_matches(suspicious: str, source: str, model: HybridModel, window: int = 40) -> list[PassageMatch]:
    suspicious_words = normalize_text(suspicious).split()
    source_words = normalize_text(source).split()
    if not suspicious_words or not source_words:
        return []
    matches: list[PassageMatch] = []
    for start in range(0, len(suspicious_words), window):
        passage = " ".join(suspicious_words[start : start + window])
        score = model.score(passage, source)
        if score >= model.threshold:
            matches.append(PassageMatch(passage, source[:240], score))
    return matches


def explain(suspicious: str, source: str, model: HybridModel) -> dict[str, object]:
    score = model.score(suspicious, source)
    matches = [asdict(match) for match in find_matches(suspicious, source, model)]
    reasons = ["high lexical overlap"] if score >= model.threshold else ["insufficient overlap for the configured threshold"]
    return {"score": score, "label": "plagiarism" if score >= model.threshold else "original", "reasons": reasons, "matches": matches}

