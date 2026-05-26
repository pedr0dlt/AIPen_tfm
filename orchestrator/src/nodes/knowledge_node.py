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
        "linux":   ["04_foothold_linux", "02_enum", "03_bruteforce"],
        "windows": ["05_foothold_windows", "02_enum", "03_bruteforce"],
        "unknown": ["04_foothold_linux", "02_enum", "03_bruteforce"],
    },
    "post-exploitation": ["07_post_exploit", "06_privesc"],
}

_PORT_FILE_PRIORITY: dict[str, dict[int, str]] = {
    "01_recon": {
        53:   "01_osint_dns.md",
        80:   "03_web_recon.md",
        443:  "03_web_recon.md",
        8080: "03_web_recon.md",
        8443: "03_web_recon.md",
    },
    "02_enum": {
        21:    "01_ftp_ssh.md",
        22:    "01_ftp_ssh.md",
        23:    "01_ftp_ssh.md",
        25:    "02_smtp_http.md",
        80:    "02_smtp_http.md",
        443:   "02_smtp_http.md",
        139:   "03_smb.md",
        445:   "03_smb.md",
        1433:  "04_sql_otros.md",
        3306:  "04_sql_otros.md",
        5432:  "04_sql_otros.md",
        27017: "04_sql_otros.md",
    },
    "04_foothold_linux": {
        21:   "01_vulns_ftp_samba.md",
        139:  "01_vulns_ftp_samba.md",
        445:  "01_vulns_ftp_samba.md",
        22:   "02_vulns_ssh_otros.md",
        23:   "02_vulns_ssh_otros.md",
        1099: "02_vulns_ssh_otros.md",
        3306: "02_vulns_ssh_otros.md",
        5432: "02_vulns_ssh_otros.md",
        80:   "03_web_sqli_upload.md",
        443:  "03_web_sqli_upload.md",
        8080: "04_web_lfi_cms.md",
        8443: "04_web_lfi_cms.md",
    },
    "05_foothold_windows": {
        139:  "01_smb_exploits.md",
        445:  "01_smb_exploits.md",
        80:   "02_http_iis_otros.md",
        443:  "02_http_iis_otros.md",
        8080: "02_http_iis_otros.md",
        8443: "02_http_iis_otros.md",
    },
    "03_bruteforce": {
        # Hydra cubre cualquier login con red abierto (ssh/ftp/smb/mysql/...)
        21:   "01_hydra.md",
        22:   "01_hydra.md",
        23:   "01_hydra.md",
        25:   "01_hydra.md",
        80:   "01_hydra.md",
        110:  "01_hydra.md",
        139:  "01_hydra.md",
        443:  "01_hydra.md",
        445:  "01_hydra.md",
        3306: "01_hydra.md",
        5432: "01_hydra.md",
    },
}


def _priority_files_for(folder: str, open_ports: list[int] | None) -> list[str]:
    """Devuelve los ficheros de `folder` prioritarios para `open_ports`."""
    mapping = _PORT_FILE_PRIORITY.get(folder, {})
    if not mapping or not open_ports:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for port in open_ports:
        pf = mapping.get(port)
        if pf and pf not in seen:
            out.append(pf)
            seen.add(pf)
    return out


_HINT_KEYWORDS: dict[str, dict[str, str]] = {
    "03_bruteforce": {
        "hydra":      "01_hydra.md",
        "bruteforce": "01_hydra.md",
        "fuerza bruta": "01_hydra.md",
        "wpscan":     "01_hydra.md",
        "msf brute":  "02_msf_brute.md",
        "msf_brute":  "02_msf_brute.md",
        "john":       "03_john_searchsploit.md",
        "searchsploit": "03_john_searchsploit.md",
    },
    "04_foothold_linux": {
        "gobuster":  "03_web_sqli_upload.md",
        "sqlmap":    "03_web_sqli_upload.md",
        "lfi":       "04_web_lfi_cms.md",
        "rfi":       "04_web_lfi_cms.md",
        "drupal":    "04_web_lfi_cms.md",
        "wordpress": "04_web_lfi_cms.md",
    },
    "02_enum": {
        "smbclient": "03_smb.md",
        "enum4linux": "03_smb.md",
    },
    "01_recon": {
        "gobuster": "03_web_recon.md",
        "whatweb":  "03_web_recon.md",
        "nikto":    "03_web_recon.md",
        "curl":     "03_web_recon.md",
    },
    # Privesc Linux — keywords típicas de escalada en sudo / SUID / GTFOBins
    "06_privesc": {
        "sudo":     "01_linux_enum_sudo_suid.md",
        "sudo -l":  "01_linux_enum_sudo_suid.md",
        "gtfobins": "01_linux_enum_sudo_suid.md",
        "suid":     "01_linux_enum_sudo_suid.md",
        "nopasswd": "01_linux_enum_sudo_suid.md",
        "ruby":     "01_linux_enum_sudo_suid.md",
        "perl":     "01_linux_enum_sudo_suid.md",
        "python":   "01_linux_enum_sudo_suid.md",
        "vim":      "01_linux_enum_sudo_suid.md",
        "find":     "01_linux_enum_sudo_suid.md",
        "less":     "01_linux_enum_sudo_suid.md",
        "more":     "01_linux_enum_sudo_suid.md",
        "awk":      "01_linux_enum_sudo_suid.md",
        "elevar":   "01_linux_enum_sudo_suid.md",
        "escalar":  "01_linux_enum_sudo_suid.md",
        "privesc":  "01_linux_enum_sudo_suid.md",
        "cron":     "02_linux_cron_kernel_lxc.md",
        "kernel":   "02_linux_cron_kernel_lxc.md",
        "lxc":      "02_linux_cron_kernel_lxc.md",
        "lxd":      "02_linux_cron_kernel_lxc.md",
    },
}


def _hint_priority(folder: str, hint: str) -> list[str]:
    """Devuelve ficheros forzados por keyword del operador."""
    if not hint:
        return []
    low = hint.lower()
    folder_map = _HINT_KEYWORDS.get(folder, {})
    out: list[str] = []
    seen: set[str] = set()
    for kw, filename in folder_map.items():
        if kw in low and filename not in seen:
            out.append(filename)
            seen.add(filename)
    return out


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
                    allowed_folders: list[str] | None = None,
                    operator_hint: str = "") -> list[tuple[str, str]]:
    store = get_store()
    if store is None or k <= 0:
        return []

    ports_str = ",".join(str(p) for p in (open_ports or [])[:20])
    output_snippet = (last_output or "")[:600]
    hint_snippet = (operator_hint or "").strip()[:300]
    query = (
        f"fase {phase} OS {os_type} puertos {ports_str}. "
        f"Salida reciente: {output_snippet}"
    )
    if hint_snippet:
        query = f"Petición del operador: {hint_snippet}. {hint_snippet}. " + query

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


def _substitute_placeholders(text: str, target_ip: str, lhost: str) -> str:
    if not text:
        return text
    if target_ip:
        for ph in ("<TARGET_IP>", "<RHOSTS>", "<TARGET>", "<IP>"):
            text = text.replace(ph, target_ip)
    if lhost:
        text = text.replace("<LHOST>", lhost)
    return text


def load_playbook(phase: str, os_type: str = "unknown",
                  open_ports: list[int] | None = None,
                  last_output: str = "",
                  target_ip: str = "",
                  lhost: str = "",
                  operator_hint: str = "") -> str:
    entry = _PHASE_FOLDERS.get(phase)
    if entry is None:
        return ""

    if isinstance(entry, dict):
        folders = entry.get(os_type, entry["unknown"])
    else:
        folders = entry

    rule_parts: list[tuple[str, str]] = []
    for folder in folders:
        hint_pf = _hint_priority(folder, operator_hint)
        port_pf = _priority_files_for(folder, open_ports)
        # El hint del operador manda: va primero.
        pf = hint_pf + [f for f in port_pf if f not in hint_pf]
        if hint_pf:
            print(f"[knowledge_node]   HINT del operador en '{folder}': {hint_pf}")
        elif port_pf:
            print(f"[knowledge_node]   Prioridad por puerto en '{folder}': {port_pf}")
        rule_parts.extend(_load_folder(folder, pf))
        if len(rule_parts) >= _MAX_FILES_PER_PHASE:
            break

    faiss_k = max(0, _MAX_FILES_PER_PHASE - 1)
    faiss_parts = _faiss_retrieve(
        phase, os_type, open_ports, last_output,
        k=faiss_k,
        allowed_folders=list(folders),
        operator_hint=operator_hint,
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
    body = "\n\n---\n\n".join(content for _, content in chosen)
    body = _substitute_placeholders(body, target_ip=target_ip, lhost=lhost)
    return header + body
