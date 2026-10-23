from __future__ import annotations

from collections import Counter
from math import sqrt

from .text import char_ngrams, normalized_levenshtein


def cosine_similarity(left: Counter[str], right: Counter[str]) -> float:
    keys = set(left) | set(right)
    numerator = sum(left[key] * right[key] for key in keys)
    denominator = sqrt(sum(value * value for value in left.values()) * sum(value * value for value in right.values()))
    return numerator / denominator if denominator else 0.0


def tfidf_similarity(left: str, right: str) -> float:
    # A two-document TF-IDF cosine is deterministic and keeps the baseline dependency-free.
    left_counts, right_counts = Counter(left.casefold().split()), Counter(right.casefold().split())
    vocabulary = set(left_counts) | set(right_counts)
    vectors = []
    for counts, other in ((left_counts, right_counts), (right_counts, left_counts)):
        vector = {}
        for token in vocabulary:
            tf = counts[token] / max(1, sum(counts.values()))
            df = int(token in counts) + int(token in other)
            vector[token] = tf * (1.0 if df == 1 else 0.0)
        vectors.append(vector)
    return cosine_similarity(Counter(vectors[0]), Counter(vectors[1]))


def ngram_similarity(left: str, right: str, n: int = 5) -> float:
    return cosine_similarity(char_ngrams(left, n), char_ngrams(right, n))


def baseline_features(left: str, right: str) -> dict[str, float]:
    return {
        "tfidf": tfidf_similarity(left, right),
        "ngram": ngram_similarity(left, right),
        "levenshtein": normalized_levenshtein(left, right),
    }

