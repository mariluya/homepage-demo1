from __future__ import annotations

import json
import os
import pickle
from functools import lru_cache

import faiss
import jieba
import numpy as np
from sentence_transformers import SentenceTransformer

from common import INDEX_DIR


@lru_cache(maxsize=1)
def resources():
    chunks = json.loads((INDEX_DIR / "chunks.json").read_text(encoding="utf-8"))
    meta = json.loads((INDEX_DIR / "meta.json").read_text(encoding="utf-8"))
    index = faiss.read_index(str(INDEX_DIR / "vectors.faiss"))
    with (INDEX_DIR / "bm25.pkl").open("rb") as handle:
        bm25 = pickle.load(handle)["bm25"]
    model = SentenceTransformer(meta["model"], trust_remote_code=True)
    return chunks, index, bm25, model


def minmax(values: dict[int, float]) -> dict[int, float]:
    if not values:
        return {}
    low, high = min(values.values()), max(values.values())
    if high <= low:
        return {key: 1.0 for key in values}
    return {key: (value - low) / (high - low) for key, value in values.items()}


def hybrid_search(query: str, vector_k: int = 20, bm25_k: int = 20, final_k: int = 6) -> list[dict]:
    chunks, index, bm25, model = resources()
    query_vector = model.encode([query], normalize_embeddings=True).astype("float32")
    vector_scores, vector_ids = index.search(query_vector, vector_k)
    vector = {int(idx): float(score) for idx, score in zip(vector_ids[0], vector_scores[0]) if idx >= 0}
    lexical_scores = bm25.get_scores(list(jieba.cut_for_search(query.lower())))
    lexical_ids = np.argsort(lexical_scores)[::-1][:bm25_k]
    lexical = {int(idx): float(lexical_scores[idx]) for idx in lexical_ids}
    v_norm, b_norm = minmax(vector), minmax(lexical)
    merged = set(vector) | set(lexical)
    ranked = sorted(merged, key=lambda idx: 0.58 * v_norm.get(idx, 0) + 0.42 * b_norm.get(idx, 0), reverse=True)
    results = []
    for idx in ranked[:final_k]:
        item = dict(chunks[idx])
        item["score"] = round(0.58 * v_norm.get(idx, 0) + 0.42 * b_norm.get(idx, 0), 4)
        results.append(item)
    return results

