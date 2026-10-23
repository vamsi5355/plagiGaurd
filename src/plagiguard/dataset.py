from __future__ import annotations

import hashlib
import json
import os
import tarfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from .models import Document, PairExample
from .text import normalize_text


class DatasetError(ValueError):
    """Raised when a dataset artifact is invalid or unsafe."""


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_archive(path: Path, expected_sha256: str) -> str:
    if not path.is_file():
        raise DatasetError(f"archive does not exist: {path}")
    actual = sha256_file(path)
    if actual.casefold() != expected_sha256.casefold():
        raise DatasetError(f"checksum mismatch: expected {expected_sha256}, got {actual}")
    return actual


def _safe_member_path(destination: Path, member_name: str) -> Path:
    target = (destination / member_name).resolve()
    root = destination.resolve()
    if os.path.commonpath((str(root), str(target))) != str(root):
        raise DatasetError(f"unsafe archive member: {member_name}")
    return target


def extract_archive(path: Path, destination: Path, expected_sha256: str | None = None) -> list[Path]:
    if expected_sha256:
        verify_archive(path, expected_sha256)
    destination.mkdir(parents=True, exist_ok=True)
    extracted: list[Path] = []
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                target = _safe_member_path(destination, info.filename)
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as source, target.open("wb") as output:
                    output.write(source.read())
                extracted.append(target)
        return extracted
    if tarfile.is_tarfile(path):
        with tarfile.open(path) as archive:
            for info in archive.getmembers():
                target = _safe_member_path(destination, info.name)
                if info.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                if not info.isfile():
                    raise DatasetError(f"unsupported archive member: {info.name}")
                target.parent.mkdir(parents=True, exist_ok=True)
                source = archive.extractfile(info)
                if source is None:
                    raise DatasetError(f"unable to read archive member: {info.name}")
                with source, target.open("wb") as output:
                    output.write(source.read())
                extracted.append(target)
        return extracted
    raise DatasetError(f"unsupported archive format: {path}")


def parse_pan_xml(path: Path) -> Document:
    try:
        root = ElementTree.parse(path).getroot()
    except ElementTree.ParseError as exc:
        raise DatasetError(f"invalid XML: {path}") from exc
    text = " ".join("".join(root.itertext()).split())
    document_id = root.attrib.get("id") or path.stem
    source_id = root.attrib.get("source-document") or root.attrib.get("source_id")
    return Document(document_id=document_id, text=text, source_id=source_id)


def load_documents(root: Path) -> list[Document]:
    documents = [parse_pan_xml(path) for path in sorted(root.rglob("*.xml"))]
    if not documents:
        raise DatasetError(f"no XML documents found under {root}")
    return documents


def build_pairs(documents: list[Document]) -> list[PairExample]:
    by_id = {doc.document_id: doc for doc in documents}
    pairs: list[PairExample] = []
    for suspicious in documents:
        if not suspicious.source_id:
            continue
        source = by_id.get(suspicious.source_id)
        if source is None:
            raise DatasetError(f"missing source {suspicious.source_id} for {suspicious.document_id}")
        pairs.append(
            PairExample(
                pair_id=f"{suspicious.document_id}::{source.document_id}",
                suspicious_id=suspicious.document_id,
                source_id=source.document_id,
                suspicious_text=suspicious.text,
                source_text=source.text,
                label=1,
            )
        )
    return pairs


def validate_pairs(pairs: list[PairExample]) -> None:
    seen: set[str] = set()
    sources: dict[str, set[str]] = {}
    for pair in pairs:
        if pair.pair_id in seen:
            raise DatasetError(f"duplicate pair: {pair.pair_id}")
        seen.add(pair.pair_id)
        if pair.label not in (0, 1):
            raise DatasetError(f"invalid label for {pair.pair_id}: {pair.label}")
        if not normalize_text(pair.suspicious_text) or not normalize_text(pair.source_text):
            raise DatasetError(f"empty document in {pair.pair_id}")
        sources.setdefault(pair.suspicious_id, set()).add(pair.source_id)
    # A suspicious document may have multiple candidate sources, but duplicate source
    # documents must not appear under different IDs in a prepared corpus.
    normalized_sources: dict[str, str] = {}
    for pair in pairs:
        key = normalize_text(pair.source_text)
        prior = normalized_sources.setdefault(key, pair.source_id)
        if prior != pair.source_id:
            raise DatasetError(f"duplicate source content: {prior} and {pair.source_id}")


def write_jsonl(pairs: list[PairExample], output: Path) -> int:
    validate_pairs(pairs)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for pair in pairs:
            handle.write(json.dumps(pair.to_dict(), ensure_ascii=False) + "\n")
    return len(pairs)

