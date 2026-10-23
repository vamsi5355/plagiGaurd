from __future__ import annotations

import re
from collections import Counter

_WORD_RE = re.compile(r"\b[\w'-]+\b", re.UNICODE)


def normalize_text(text: str) -> str:
    return " ".join(text.casefold().split())


def words(text: str) -> list[str]:
    return _WORD_RE.findall(normalize_text(text))


def word_ngrams(text: str, n: int = 3) -> set[tuple[str, ...]]:
    tokens = words(text)
    return {tuple(tokens[i : i + n]) for i in range(max(0, len(tokens) - n + 1))}


def char_ngrams(text: str, n: int = 5) -> Counter[str]:
    normalized = normalize_text(text)
    return Counter(normalized[i : i + n] for i in range(max(0, len(normalized) - n + 1)))


def normalized_levenshtein(left: str, right: str) -> float:
    a, b = normalize_text(left), normalize_text(right)
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    previous = list(range(len(b) + 1))
    for i, char_a in enumerate(a, 1):
        current = [i]
        for j, char_b in enumerate(b, 1):
            current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (char_a != char_b)))
        previous = current
    distance = previous[-1]
    return 1.0 - distance / max(len(a), len(b))
