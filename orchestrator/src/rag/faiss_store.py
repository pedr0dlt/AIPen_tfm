from __future__ import annotations

import os
import json
import threading
from typing import Optional

# Modelo multilingüe pequeño
_DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

_DEFAULT_INDEX_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "rag_index")
)

_lock = threading.Lock()
_instance: Optional["FaissStore"] = None
_disabled: bool = False


class FaissStore:
    def __init__(self, index_dir: str = _DEFAULT_INDEX_DIR,
                 model_name: str = _DEFAULT_MODEL):
        import faiss
        from sentence_transformers import SentenceTransformer

        index_path = os.path.join(index_dir, "index.faiss")
        meta_path = os.path.join(index_dir, "metadata.json")

        if not os.path.exists(index_path) or not os.path.exists(meta_path):
            raise FileNotFoundError(
                f"Índice FAISS no encontrado en {index_dir}. "
                f"Construye antes con:\n"
                f"  docker exec tfm_orchestrator python -m src.rag.build_index"
            )

        import faiss as _faiss
        self.index = _faiss.read_index(index_path)
        with open(meta_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

        if self.index.ntotal != len(self.metadata):
            raise RuntimeError(
                f"Desajuste: índice tiene {self.index.ntotal} vectores pero "
                f"metadata tiene {len(self.metadata)} entradas. Reconstruye."
            )

        self.model = SentenceTransformer(model_name)
        print(f"[FaissStore] Cargado: {self.index.ntotal} chunks, "
              f"dim={self.index.d}, modelo={model_name.split('/')[-1]}")

    def retrieve(self, query: str, k: int = 2) -> list[dict]:
        import numpy as np

        if not query or not query.strip() or k <= 0:
            return []

        emb = self.model.encode(
            [f"query: {query}"],
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        emb = np.asarray(emb, dtype="float32")

        k = min(k, self.index.ntotal)
        scores, ids = self.index.search(emb, k)

        results: list[dict] = []
        for score, idx in zip(scores[0], ids[0]):
            if idx == -1 or idx >= len(self.metadata):
                continue
            meta = self.metadata[idx]
            results.append({
                "filepath": meta["filepath"],
                "content": meta["content"],
                "score": float(score),
            })
        return results


def get_store() -> Optional[FaissStore]:
    global _instance, _disabled
    if _disabled:
        return None
    if _instance is not None:
        return _instance
    with _lock:
        if _instance is not None:
            return _instance
        if _disabled:
            return None
        try:
            _instance = FaissStore()
            return _instance
        except Exception as e:
            print(f"[FaissStore] Deshabilitado (fallback a reglas): {e}")
            _disabled = True
            return None
