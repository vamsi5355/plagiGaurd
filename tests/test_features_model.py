from plagiguard.features import baseline_features
from plagiguard.model import split_by_source, train_hybrid
from plagiguard.models import PairExample


def test_features_reward_identical_text():
    features = baseline_features("The same words here", "The same words here")
    assert features["levenshtein"] == 1.0
    assert features["ngram"] > 0


def test_split_keeps_sources_separate_and_model_round_trips(tmp_path):
    rows = [
        PairExample("a", "a", "source-a", "copied words", "copied words", 1),
        PairExample("b", "b", "source-b", "different", "original text", 0),
    ]
    train, validation = split_by_source(rows, validation_fraction=0.5)
    assert {r.source_id for r in train}.isdisjoint({r.source_id for r in validation})
    model = train_hybrid(rows, {"fixture": True})
    path = tmp_path / "model.json"
    model.save(path)
    loaded = model.load(path)
    assert loaded.trained is True
    assert loaded.metadata == {"fixture": True}

