# PlagiGuard

PlagiGuard is a modular plagiarism-detection toolkit. It provides a reproducible
dataset pipeline for PAN-style corpora, classical text-similarity baselines, a
leakage-aware supervised hybrid model, and a small FastAPI service for analysis.

## Current implementation status

The code is implemented and tested against small local fixtures. The real PAN-PC-11
corpus is **not included or downloaded** by this repository. See
[`IMPLEMENTATION_STATUS.md`](IMPLEMENTATION_STATUS.md) for the exact verification
state and the distinction between code, trained artifacts, and evaluated models.

## Quick start

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
uvicorn plagiguard.api:app --reload
```

The API exposes `/health`, `/ready`, `/metadata`, and `/analyze`. The analysis
endpoint accepts plain text or uploaded TXT/Markdown/DOCX files and returns a
similarity score, label, matched passages, and explanations.

## Dataset provenance

PAN Plagiarism Corpus 2011 (PAN-PC-11) was assembled by Martin Potthast, Benno
Stein, Andreas Eiselt, Alberto Barrón-Cedeño, and Paolo Rosso for plagiarism
detection evaluation. The official cited record is Zenodo DOI
`10.5281/zenodo.3250095`; consult that record for the authoritative download,
license, citation, and version terms before acquisition. This project does not
redistribute the corpus. Its synthetic and manually inserted plagiarism examples
are a benchmark, not a representative sample of all real-world writing, and
results must not be treated as legal or authorship conclusions.

Acquire the corpus from its official record, record the URL and SHA-256 in a
local manifest, and run the checksum-aware pipeline:

```bash
python -m plagiguard.cli verify-archive data/raw/pan-pc-11.zip --sha256 <digest>
python -m plagiguard.cli extract-archive data/raw/pan-pc-11.zip data/extracted --sha256 <digest>
python -m plagiguard.cli build-jsonl data/extracted data/processed/examples.jsonl
```

The benchmark can contain synthetic and obfuscated examples, so metrics should
not be generalized to real-world authorship or legal conclusions.
