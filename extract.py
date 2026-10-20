from __future__ import annotations

import json
from pathlib import Path

import pdfplumber
from pypdf import PdfReader

from common import DATA_DIR, EXTRACTED_DIR, clean_text, ensure_dirs, load_companies


def normalize_table(table: list[list[str | None]]) -> list[list[str]]:
    rows = []
    for row in table or []:
        values = [clean_text(cell or "") for cell in row]
        if any(values):
            rows.append(values)
    return rows


def extract_company(company: dict) -> Path:
    source = DATA_DIR / company["name"] / "2026_半年报.pdf"
    if not source.exists():
        raise FileNotFoundError(source)
    reader = PdfReader(str(source))
    output = []
    with pdfplumber.open(source) as plumber:
        page_count = max(len(reader.pages), len(plumber.pages))
        for index in range(page_count):
            text = ""
            if index < len(reader.pages):
                text = clean_text(reader.pages[index].extract_text() or "")
            tables = []
            if index < len(plumber.pages):
                for table in plumber.pages[index].extract_tables() or []:
                    normalized = normalize_table(table)
                    if normalized:
                        tables.append(normalized)
            output.append({
                "company": company["name"],
                "code": company["code"],
                "year": 2026,
                "report": "半年度报告",
                "page": index + 1,
                "text": text,
                "tables": tables,
                "source_pdf": str(source),
            })
    target = EXTRACTED_DIR / f'{company["code"]}_{company["name"]}.json'
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def main() -> None:
    ensure_dirs()
    for company in load_companies():
        try:
            target = extract_company(company)
            print("完成", target.name)
        except FileNotFoundError:
            print("跳过，缺少PDF", company["name"])


if __name__ == "__main__":
    main()

