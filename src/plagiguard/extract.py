from __future__ import annotations

import io
from pathlib import Path


class ExtractionError(ValueError):
    """Raised when a supported document cannot be extracted."""


def extract_text(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.casefold()
    if suffix in {".txt", ".md", ".markdown"}:
        text = content.decode("utf-8")
    elif suffix == ".docx":
        try:
            from docx import Document as WordDocument

            document = WordDocument(io.BytesIO(content))
            text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        except ImportError as exc:
            raise ExtractionError("DOCX support requires python-docx") from exc
        except Exception as exc:
            raise ExtractionError("invalid DOCX document") from exc
    else:
        raise ExtractionError("supported formats are TXT, Markdown, and DOCX")
    text = text.strip()
    if not text:
        raise ExtractionError("document is empty")
    return text
