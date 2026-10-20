from __future__ import annotations

import json
import os
import pickle

import faiss
import jieba
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from common import INDEX_DIR, ROOT, ensure_dirs


def load_chunks() -> list[dict]:
    with (ROOT / "chunks.jsonl").open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main() -> None:
    ensure_dirs()
    chunks = load_chunks()
    texts = [f'公司：{c["company"]}\n章节：{c["section"]}\n{c["text"]}' for c in chunks]
    model_name = os.getenv("EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-0.6B")
    device = "cuda"
    model = SentenceTransformer(model_name, device=device, trust_remote_code=True)
    vectors = model.encode(
        texts, batch_size=32 if device == "cuda" else 2,
        normalize_embeddings=True, show_progress_bar=True,
    ).astype("float32")
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    faiss.write_index(index, str(INDEX_DIR / "vectors.faiss"))
    tokens = [list(jieba.cut_for_search(text.lower())) for text in texts]
    bm25 = BM25Okapi(tokens)
    with (INDEX_DIR / "bm25.pkl").open("wb") as handle:
        pickle.dump({"bm25": bm25, "tokens": tokens}, handle)
    (INDEX_DIR / "chunks.json").write_text(
        json.dumps(chunks, ensure_ascii=False), encoding="utf-8"
    )
    (INDEX_DIR / "meta.json").write_text(json.dumps({
        "model": model_name, "dimensions": int(vectors.shape[1]), "chunks": len(chunks)
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"索引完成：{len(chunks):,} 块，{vectors.shape[1]} 维")


if __name__ == "__main__":
    main()

