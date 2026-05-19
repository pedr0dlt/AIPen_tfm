from __future__ import annotations

import os
import json
import sys


_PLAYBOOKS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "playbooks")
)
_OUTPUT_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "rag_index")
)

_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
_EMBED_CONTEXT_CHARS = 1800


def _iter_playbook_files() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for root, _dirs, files in os.walk(_PLAYBOOKS_DIR):
        for fname in sorted(files):
            if not fname.endswith(".md"):
                continue
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, _PLAYBOOKS_DIR).replace(os.sep, "/")
            if "/" not in rel:
                continue
            with open(full, "r", encoding="utf-8") as f:
                content = f.read()
            out.append((rel, content))
    return out


def _index_is_fresh() -> bool:
    index_path = os.path.join(_OUTPUT_DIR, "index.faiss")
    meta_path = os.path.join(_OUTPUT_DIR, "metadata.json")
    if not (os.path.exists(index_path) and os.path.exists(meta_path)):
        return False
    index_mtime = os.path.getmtime(index_path)
    for root, _dirs, files in os.walk(_PLAYBOOKS_DIR):
        for fname in files:
            if not fname.endswith(".md"):
                continue
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, _PLAYBOOKS_DIR).replace(os.sep, "/")
            if "/" not in rel:
                continue
            if os.path.getmtime(full) > index_mtime:
                return False
    return True


def main() -> int:
    if "--if-needed" in sys.argv and _index_is_fresh():
        print("[build_index] Índice ya al día. Omitiendo reconstrucción.")
        return 0

    try:
        import faiss
        import numpy as np
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        print(f"[build_index] Falta dependencia: {e}")
        print("Instala: pip install faiss-cpu sentence-transformers")
        return 1

    files = _iter_playbook_files()
    if not files:
        print(f"[build_index] No se encontraron playbooks en {_PLAYBOOKS_DIR}")
        return 1
    print(f"[build_index] {len(files)} playbooks encontrados:")
    for rel, _ in files:
        print(f"   - {rel}")

    print(f"\n[build_index] Cargando modelo: {_MODEL_NAME} (1ª vez descarga ~470 MB)...")
    model = SentenceTransformer(_MODEL_NAME)

    texts_for_embedding = [
        f"passage: {rel}\n\n{content[:_EMBED_CONTEXT_CHARS]}"
        for rel, content in files
    ]

    print("[build_index] Calculando embeddings...")
    embeddings = model.encode(
        texts_for_embedding,
        normalize_embeddings=True,
        show_progress_bar=True,
        batch_size=8,
    )
    embeddings = np.asarray(embeddings, dtype="float32")
    dim = int(embeddings.shape[1])

    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    print(f"[build_index] Índice creado: {index.ntotal} vectores, dim={dim}")

    os.makedirs(_OUTPUT_DIR, exist_ok=True)
    faiss.write_index(index, os.path.join(_OUTPUT_DIR, "index.faiss"))

    metadata = [
        {"filepath": rel, "content": content}
        for rel, content in files
    ]
    with open(os.path.join(_OUTPUT_DIR, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"\n[build_index] OK. Guardado en {_OUTPUT_DIR}")
    print(f"             - index.faiss ({index.ntotal} vectores)")
    print(f"             - metadata.json ({len(metadata)} entradas)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
