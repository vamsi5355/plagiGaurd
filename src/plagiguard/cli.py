from __future__ import annotations

import argparse
from pathlib import Path

from .dataset import build_pairs, extract_archive, load_documents, verify_archive, write_jsonl


def main() -> None:
    parser = argparse.ArgumentParser(prog="plagiguard")
    subparsers = parser.add_subparsers(dest="command", required=True)
    verify = subparsers.add_parser("verify-archive")
    verify.add_argument("archive", type=Path)
    verify.add_argument("--sha256", required=True)
    extract = subparsers.add_parser("extract-archive")
    extract.add_argument("archive", type=Path)
    extract.add_argument("destination", type=Path)
    extract.add_argument("--sha256")
    jsonl = subparsers.add_parser("build-jsonl")
    jsonl.add_argument("documents", type=Path)
    jsonl.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.command == "verify-archive":
        print(verify_archive(args.archive, args.sha256))
    elif args.command == "extract-archive":
        print(f"extracted {len(extract_archive(args.archive, args.destination, args.sha256))} files")
    elif args.command == "build-jsonl":
        print(write_jsonl(build_pairs(load_documents(args.documents)), args.output))

