from __future__ import annotations

import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
EXTRACTED_DIR = ROOT / "extracted"
INDEX_DIR = ROOT / "index_data"
EVAL_DIR = ROOT / "evaluation"


def ensure_dirs() -> None:
    for path in (DATA_DIR, EXTRACTED_DIR, INDEX_DIR, EVAL_DIR):
        path.mkdir(parents=True, exist_ok=True)


def load_companies() -> list[dict]:
    return json.loads((ROOT / "companies.json").read_text(encoding="utf-8"))["companies"]


def clean_text(text: str) -> str:
    text = text.replace("\u3000", " ").replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def env(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)

