import hashlib
import zipfile

import pytest

from plagiguard.dataset import (
    DatasetError,
    build_pairs,
    extract_archive,
    parse_pan_xml,
    verify_archive,
    write_jsonl,
)


def test_archive_checksum_and_safe_extraction(tmp_path):
    archive = tmp_path / "fixture.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("docs/source.xml", '<document id="s"><text>Source text</text></document>')
        handle.writestr("docs/suspicious.xml", '<document id="p" source-document="s"><text>Copied text</text></document>')
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    destination = tmp_path / "out"
    assert verify_archive(archive, digest) == digest
    assert len(extract_archive(archive, destination, digest)) == 2
    docs = [parse_pan_xml(path) for path in sorted(destination.rglob("*.xml"))]
    pairs = build_pairs(docs)
    output = tmp_path / "pairs.jsonl"
    assert write_jsonl(pairs, output) == 1
    assert '"label": 1' in output.read_text()


def test_path_traversal_is_rejected(tmp_path):
    archive = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("../escape.txt", "bad")
    with pytest.raises(DatasetError, match="unsafe"):
        extract_archive(archive, tmp_path / "out")
