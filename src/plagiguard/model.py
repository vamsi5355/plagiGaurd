from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path

from .features import baseline_features
from .models import PairExample


@dataclass
class HybridModel:
    weights: dict[str, float]
    bias: float
    threshold: float = 0.5
    trained: bool = False
    metadata: dict[str, object] | None = None

    def score(self, suspicious_text: str, source_text: str) -> float:
        features = baseline_features(suspicious_text, source_text)
        raw = self.bias + sum(self.weights.get(name, 0.0) * value for name, value in features.items())
        return 1.0 / (1.0 + pow(2.718281828, -raw))

    def predict(self, suspicious_text: str, source_text: str) -> int:
        return int(self.score(suspicious_text, source_text) >= self.threshold)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> HybridModel:
        return cls(**json.loads(path.read_text(encoding="utf-8")))


def split_by_source(examples: list[PairExample], validation_fraction: float = 0.2) -> tuple[list[PairExample], list[PairExample]]:
    if not 0 < validation_fraction < 1:
        raise ValueError("validation_fraction must be between 0 and 1")
    source_ids = sorted({example.source_id for example in examples})
    cutoff = max(1, round(len(source_ids) * (1 - validation_fraction)))
    train_sources = set(source_ids[:cutoff])
    train = [example for example in examples if example.source_id in train_sources]
    validation = [example for example in examples if example.source_id not in train_sources]
    return train, validation


def train_hybrid(examples: Iterable[PairExample], metadata: dict[str, object] | None = None) -> HybridModel:
    rows = list(examples)
    if not rows:
        raise ValueError("cannot train on empty examples")
    names = ("tfidf", "ngram", "levenshtein")
    sums = {name: 0.0 for name in names}
    positive = 0
    for row in rows:
        features = baseline_features(row.suspicious_text, row.source_text)
        sign = 1.0 if row.label else -1.0
        positive += row.label
        for name in names:
            sums[name] += sign * features[name]
    weights = {name: sums[name] / len(rows) for name in names}
    bias = (positive / len(rows) - 0.5) * 2
    return HybridModel(weights=weights, bias=bias, trained=True, metadata=metadata)
