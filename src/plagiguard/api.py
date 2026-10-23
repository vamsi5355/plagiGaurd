from __future__ import annotations

import os

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from .extract import ExtractionError, extract_text
from .matching import explain
from .model import HybridModel

MAX_FILE_BYTES = int(os.getenv("PLAGIGUARD_MAX_FILE_BYTES", str(2 * 1024 * 1024)))
app = FastAPI(title="PlagiGuard", version="0.1.0")
model = HybridModel(weights={"tfidf": 1.0, "ngram": 1.0, "levenshtein": 1.0}, bias=0.0)


class AnalyzeRequest(BaseModel):
    suspicious_text: str = Field(min_length=1, max_length=200_000)
    source_text: str = Field(min_length=1, max_length=200_000)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, object]:
    return {"ready": True, "model_trained": model.trained}


@app.get("/metadata")
def metadata() -> dict[str, object]:
    return {"name": "PlagiGuard", "version": "0.1.0", "model_trained": model.trained, "max_file_bytes": MAX_FILE_BYTES}


@app.post("/analyze")
def analyze(request: AnalyzeRequest) -> dict[str, object]:
    return explain(request.suspicious_text, request.source_text, model)


@app.post("/analyze-file")
async def analyze_file(
    suspicious: UploadFile = File(...), source: UploadFile = File(...)
) -> dict[str, object]:
    suspicious_bytes = await suspicious.read(MAX_FILE_BYTES + 1)
    source_bytes = await source.read(MAX_FILE_BYTES + 1)
    if len(suspicious_bytes) > MAX_FILE_BYTES or len(source_bytes) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="file exceeds configured size limit")
    try:
        suspicious_text = extract_text(suspicious.filename or "", suspicious_bytes)
        source_text = extract_text(source.filename or "", source_bytes)
    except ExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return explain(suspicious_text, source_text, model)
