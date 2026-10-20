from __future__ import annotations

import json
import re

from langchain_text_splitters import RecursiveCharacterTextSplitter

from common import EXTRACTED_DIR, ROOT, clean_text, ensure_dirs

SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=120,
    separators=["\n\n", "\n", "。", "；", "，", " "],
)


def guess_section(text: str) -> str:
    for line in text.splitlines()[:8]:
        line = clean_text(line)
        if 3 <= len(line) <= 40 and re.search(r"(章|节|情况|分析|财务|收入|利润|现金流|风险)", line):
            return line
    return "正文"


def table_chunks(record: dict, table_index: int, table: list[list[str]]) -> list[dict]:
    if not table:
        return []
    header = table[0]
    name = " / ".join(cell for cell in header if cell)[:100] or f"表{table_index}"
    chunks = []
    for row_index, row in enumerate(table[1:] or table):
        pairs = []
        for col, value in enumerate(row):
            if not value:
                continue
            label = header[col] if col < len(header) and header[col] else f"列{col + 1}"
            pairs.append(f"{label}: {value}")
        text = f"表名: {name}\n" + "\n".join(pairs)
        chunks.append({
            "company": record["company"], "code": record["code"],
            "year": record["year"], "report": record["report"],
            "section": name, "page": record["page"],
            "content_type": "table_row", "table_index": table_index,
            "row_index": row_index, "text": clean_text(text),
            "source_pdf": record["source_pdf"],
        })
    return chunks


def main() -> None:
    ensure_dirs()
    chunks = []
    for path in sorted(EXTRACTED_DIR.glob("*.json")):
        records = json.loads(path.read_text(encoding="utf-8"))
        for record in records:
            section = guess_section(record["text"])
            for part in SPLITTER.split_text(record["text"]):
                chunks.append({
                    "company": record["company"], "code": record["code"],
                    "year": record["year"], "report": record["report"],
                    "section": section, "page": record["page"],
                    "content_type": "text", "text": clean_text(part),
                    "source_pdf": record["source_pdf"],
                })
            for table_index, table in enumerate(record["tables"], 1):
                chunks.extend(table_chunks(record, table_index, table))
    target = ROOT / "chunks.jsonl"
    with target.open("w", encoding="utf-8") as handle:
        for chunk_id, chunk in enumerate(chunks):
            chunk["chunk_id"] = f"c{chunk_id:07d}"
            handle.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    print(f"写入 {len(chunks):,} 块：{target}")


if __name__ == "__main__":
    main()

