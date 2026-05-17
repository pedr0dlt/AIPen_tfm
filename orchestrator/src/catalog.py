from __future__ import annotations

import os
from pathlib import Path
from typing import Any

_CATALOG_PATH = Path(
    os.getenv("EXPLOIT_CATALOG", "/data/exploit_catalog.yaml")
)

_catalog_cache: list[dict] | None = None


def _load_yaml() -> list[dict]:
    if not _CATALOG_PATH.exists():
        print(f"[catalog] AVISO: catálogo no encontrado en {_CATALOG_PATH}")
        return []
    try:
        import yaml
    except ImportError:
        print("[catalog] AVISO: pyyaml no instalado, catálogo deshabilitado.")
        return []
    try:
        with open(_CATALOG_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data.get("exploits", []) or []
    except Exception as e:
        print(f"[catalog] ERROR cargando {_CATALOG_PATH}: {e}")
        return []


def load_catalog() -> list[dict]:
    global _catalog_cache
    if _catalog_cache is None:
        _catalog_cache = _load_yaml()
        if _catalog_cache:
            print(f"[catalog] {len(_catalog_cache)} entradas cargadas desde {_CATALOG_PATH}")
    return _catalog_cache


def _entry_applies(entry: dict, port: int, os_type: str) -> bool:
    if port not in entry.get("ports", []):
        return False
    entry_os = entry.get("os", []) or []
    if "any" in entry_os:
        return True
    if os_type in (None, "", "unknown"):
        return True 
    return os_type in entry_os


def applicable_entries(ports: list[int] | None,
                       os_type: str = "unknown") -> list[dict]:
    if not ports:
        return []
    catalog = load_catalog()
    out: list[dict] = []
    seen_ids: set[str] = set()
    for port in ports:
        for entry in catalog:
            if entry["id"] in seen_ids:
                continue
            if _entry_applies(entry, port, os_type):
                out.append(entry)
                seen_ids.add(entry["id"])
    return out


def applicable_ids(ports: list[int] | None,
                   os_type: str = "unknown") -> list[str]:
    return [e["id"] for e in applicable_entries(ports, os_type)]


def lookup(exploit_id: str) -> dict | None:
    if not exploit_id:
        return None
    for entry in load_catalog():
        if entry["id"] == exploit_id:
            return entry
    return None


def render_msfconsole(entry: dict,
                      target: str,
                      lhost: str = "") -> str:
    msf = entry.get("metasploit", {}) or {}
    vars_dict = {
        "module": msf.get("module", ""),
        "target": target,
        "lhost": lhost,
        "payload": msf.get("payload", "") or "",
    }
    raw_cmds: list[str] = entry.get("commands", []) or []
    rendered = []
    for cmd in raw_cmds:
        try:
            rendered.append(cmd.format(**vars_dict))
        except KeyError as e:
            print(f"[catalog] placeholder {e} no soportado en '{cmd[:60]}'")
            rendered.append(cmd)
    chain = "; ".join(rendered)
    return f'msfconsole -q -x "{chain}"'


def format_for_prompt(entries: list[dict]) -> str:
    if not entries:
        return "(ningún exploit aplicable — completa el recon primero con nmap)"
    lines = []
    for e in entries:
        ports = ",".join(str(p) for p in e.get("ports", []))
        name = (e.get("name") or "").strip()
        lines.append(f"  {e['id']:<32} (p{ports}) — {name}")
    return "\n".join(lines)
