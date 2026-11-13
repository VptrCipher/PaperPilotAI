import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

import pymupdf
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import CHUNK_OVERLAP, CHUNK_SIZE, MAX_PAGES, MAX_TEXT_CHARS, MAX_UPLOAD_MB

HEADING = re.compile(
    r"^(?:\d+(?:\.\d+)*\.?\s+)?"
    r"(abstract|introduction|background|related work|methods?|materials and methods|"
    r"methodology|results|discussion|conclusions?|limitations|references)\s*[:.]?$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Paper:
    document_id: str
    filename: str
    page_count: int
    chunks: list[dict]


def document_id(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract_paper(data: bytes, filename: str) -> Paper:
    if not data:
        raise ValueError("The file is empty. Choose a text-based research PDF.")
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise ValueError(f"Choose a PDF no larger than {MAX_UPLOAD_MB} MB.")
    if not data[:1024].lstrip().startswith(b"%PDF-"):
        raise ValueError("The selected file does not have a valid PDF header.")

    digest = document_id(data)
    name = Path(filename).name
    chunks = []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    try:
        with pymupdf.open(stream=data, filetype="pdf") as pdf:
            if pdf.needs_pass:
                raise ValueError("This PDF is password-protected. Upload an unlocked copy.")
            page_count = len(pdf)
            if page_count > MAX_PAGES:
                raise ValueError(f"Please use a paper with {MAX_PAGES} pages or fewer.")
            section = ""
            characters = 0
            for page in pdf:
                text = page.get_text(sort=True).replace("\x00", "")
                characters += len(text)
                if characters > MAX_TEXT_CHARS:
                    raise ValueError("This document contains too much text. Use a shorter paper.")
                sections = []
                lines = []
                for line in text.splitlines():
                    clean = re.sub(r"[ \t]+", " ", line).strip()
                    match = HEADING.fullmatch(clean)
                    if match:
                        sections.append((section, "\n".join(lines)))
                        section = match[1]
                        lines = []
                    lines.append(clean)
                sections.append((section, "\n".join(lines)))
                for heading, content in sections:
                    for chunk in splitter.split_text(content):
                        chunks.append({
                            "id": f"{page.number + 1}-{len(chunks) + 1}",
                            "text": chunk,
                            "page": page.number + 1,
                            "section": heading,
                            "document_id": digest,
                            "filename": name,
                        })
    except (pymupdf.FileDataError, RuntimeError) as exc:
        raise ValueError("The PDF could not be read. Open it locally or try another copy.") from exc

    if sum(char.isalnum() for chunk in chunks for char in chunk["text"]) < 40:
        raise ValueError("Too little text was extracted. Upload a text-based PDF. Scans need OCR first.")
    return Paper(digest, name, page_count, chunks)
