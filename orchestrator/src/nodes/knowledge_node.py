from __future__ import annotations

import os

from src.rag.faiss_store import get_store


_PLAYBOOKS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "data", "playbooks"
)

_MAX_CHARS_PER_FILE = 3200

_MAX_FILES_PER_PHASE = 2

_PHASE_FOLDERS: dict[str, list[str] | dict] = {
    "recon": ["01_recon"],
    "exploitation": {
        "linux":   ["04_foothold_linux", "02_enum"],
        "windows": ["05_foothold_windows", "02_enum"],
        "unknown": ["04_foothold_linux", "02_enum"],
    },
    "post-exploitation": ["07_post_exploit"],
}

_PORT_FILE_PRIORITY: dict[int, str] = {
    21:   "01_vulns_ftp_samba.md",
    22:   "02_vulns_ssh_otros.md",
    23:   "02_vulns_ssh_otros.md",
    25:   "02_smtp_http.md",
    80:   "03_web_sqli_upload.md",
    139:  "01_vulns_ftp_samba.md",
    443:  "03_web_sqli_upload.md",
    445:  "01_vulns_ftp_samba.md",
    1099: "02_vulns_ssh_otros.md",
    3306: "04_sql_otros.md",
    5432: "04_sql_otros.md",
    8080: "02_http_iis_otros.md",
    8443: "02_http_iis_otros.md",
}


def _load_folder(folder: str, priority_files: list[str]) -> list[tuple[str, str]]:
    folder_path = os.path.join(_PLAYBOOKS_DIR, folder)
    if not os.path.isdir(folder_path):
        return [(folder, f"[knowledge_node] Carpeta '{folder}' no encontrada en {folder_path}")]

    all_files = sorted(f for f in os.listdir(folder_path) if f.endswith(".md"))

    ordered: list[str] = []
    for pf in priority_files:
        if pf in all_files:
            ordered.append(pf)
    for f in all_files:
        if f not in ordered:
            ordered.append(f)

    parts: list[tuple[str, str]] = []
    for filename in ordered:
        path = os.path.join(folder_path, filename)
        rel = f"{folder}/{filename}"
        try:
            with open(path, "r", encoding="utf-8") as fh:
                content = fh.read()
            if len(content) > _MAX_CHARS_PER_FILE:
                content = content[:_MAX_CHARS_PER_FILE] + "\n\n...[truncado]..."
            parts.append((rel, content))
        except OSError as e:
            parts.append((rel, f"[knowledge_node] Error leyendo '{filename}': {e}"))

    return parts


def _faiss_retrieve(phase: str, os_type: str,
                    open_ports: list[int] | None,
                    last_output: str,
                    k: int,
                    allowed_folders: list[str] | None = None) -> list[tuple[str, str]]:
    store = get_store()
    if store is None or k <= 0:
        return []

    ports_str = ",".join(str(p) for p in (open_ports or [])[:20])
    output_snippet = (last_output or "")[:600]
    query = (
        f"fase {phase} OS {os_type} puertos {ports_str}. "
        f"Salida reciente: {output_snippet}"
    )

    over_k = k * 4 if allowed_folders else k
    try:
        hits = store.retrieve(query, k=over_k)
    except Exception as e:
        print(f"[knowledge_node] FAISS error: {e}. Fallback a reglas.")
        return []

    if allowed_folders:
        prefixes = tuple(f + "/" for f in allowed_folders)
        before = len(hits)
        hits = [h for h in hits if h["filepath"].startswith(prefixes)]
        if before != len(hits):
            print(f"[knowledge_node]   FAISS filtrado por fase: "
                  f"{before} → {len(hits)} hits (allowed={allowed_folders})")

    hits = hits[:k]

    out: list[tuple[str, str]] = []
    for h in hits:
        content = h["content"]
        if len(content) > _MAX_CHARS_PER_FILE:
            content = content[:_MAX_CHARS_PER_FILE] + "\n\n...[truncado]..."
        out.append((h["filepath"], content))
        print(f"[knowledge_node]   FAISS hit: {h['filepath']} (score={h['score']:.3f})")
    return out


def load_playbook(phase: str, os_type: str = "unknown",
                  open_ports: list[int] | None = None,
                  last_output: str = "") -> str:
    entry = _PHASE_FOLDERS.get(phase)
    if entry is None:
        return ""

    if isinstance(entry, dict):
        folders = entry.get(os_type, entry["unknown"])
    else:
        folders = entry

    priority_files: list[str] = []
    if open_ports:
        seen: set[str] = set()
        for port in open_ports:
            pf = _PORT_FILE_PRIORITY.get(port)
            if pf and pf not in seen:
                priority_files.append(pf)
                seen.add(pf)

    rule_parts: list[tuple[str, str]] = []
    for folder in folders:
        rule_parts.extend(_load_folder(folder, priority_files))
        if len(rule_parts) >= _MAX_FILES_PER_PHASE:
            break

    faiss_k = max(0, _MAX_FILES_PER_PHASE - 1)
    faiss_parts = _faiss_retrieve(
        phase, os_type, open_ports, last_output,
        k=faiss_k,
        allowed_folders=list(folders),
    )

    chosen: list[tuple[str, str]] = []
    seen_paths: set[str] = set()

    def _add(path: str, content: str) -> None:
        if path in seen_paths:
            return
        if len(chosen) >= _MAX_FILES_PER_PHASE:
            return
        chosen.append((path, content))
        seen_paths.add(path)

    if rule_parts:
        _add(*rule_parts[0])
    for path, content in faiss_parts:
        _add(path, content)
    for path, content in rule_parts[1:]:
        _add(path, content)

    loaded_names = ", ".join(name for name, _ in chosen) or "(ninguno)"
    total_chars = sum(len(content) for _, content in chosen)
    used_faiss = "✓" if faiss_parts else "✗"
    print(f"[knowledge_node] Fase='{phase}' OS='{os_type}' FAISS={used_faiss} "
          f"playbooks=[{loaded_names}] ({total_chars} chars)")

    header = "### PLAYBOOK DE REFERENCIA — guía táctica de la fase actual:\n\n"
    return header + "\n\n---\n\n".join(content for _, content in chosen)
