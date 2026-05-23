"""
Generador del informe final del pentest — F5.

Toma el estado final tras la ejecución del grafo LangGraph y emite un
fichero Markdown en `/data/reports/<timestamp>_<target>.md` con:

  - Resumen ejecutivo (target, OS, comprometido, creds, sesión)
  - Reconocimiento (puertos abiertos)
  - Explotación (sesión activa si la hay)
  - Credenciales y hashes desglosados por tipo (passwd / shadow / ntlm)
  - Punteros a los logs de cada intento msfconsole

El informe queda como evidencia de ejecución del agente — pensado tanto
para defensa académica como para entregar al cliente en un pentest real.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

# Bind mount en docker-compose: ./data:/data
_REPORTS_DIR = "/data/reports"
_EXPLOIT_LOG_DIR = "/logs/exploit_attempts"


def _safe(s: str | None) -> str:
    """Sanitiza un string para Markdown: sin saltos de línea, sin trim."""
    return (s or "").replace("\n", " ").strip()


def _bucket_credentials(creds: list[str]) -> dict[str, list[str]]:
    """
    Agrupa las credenciales por prefijo (passwd:, shadow:, ntlm:, ...).
    Si la entrada no tiene prefijo conocido, va a 'otros'.
    """
    out: dict[str, list[str]] = {}
    for c in creds:
        prefix = c.split(":", 1)[0] if ":" in c else "otros"
        out.setdefault(prefix, []).append(c)
    return out


def generate_report(state: dict[str, Any]) -> str:
    """
    Crea un informe Markdown a partir del estado final del agente.
    Devuelve la ruta del fichero generado o string vacío si falla.
    """
    target = _safe(state.get("target_ip")) or "unknown"
    safe_target = target.replace("/", "_").replace(":", "_")
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(_REPORTS_DIR, f"{ts}_{safe_target}.md")

    try:
        os.makedirs(_REPORTS_DIR, exist_ok=True)
    except OSError as e:
        print(f"[report] No se pudo crear {_REPORTS_DIR}: {e}")
        return ""

    # Datos del estado final
    compromised = state.get("is_compromised", False)
    os_type = _safe(state.get("os_type")) or "unknown"
    phase = _safe(state.get("current_phase")) or "unknown"
    ports = state.get("discovered_ports") or []
    creds = state.get("acquired_credentials") or []
    last_session_id = state.get("last_session_id", 0) or 0
    lhost = _safe(state.get("lhost"))

    md: list[str] = []

    # ============== Cabecera ==============
    md.append(f"# Informe de pentest — `{target}`")
    md.append("")
    md.append(f"_Generado: **{ts} UTC** por el agente AIPen_")
    md.append("")
    md.append("---")
    md.append("")

    # ============== Resumen ejecutivo ==============
    md.append("## Resumen ejecutivo")
    md.append("")
    md.append("| Métrica | Valor |")
    md.append("|---|---|")
    md.append(f"| Objetivo | `{target}` |")
    md.append(f"| OS detectado | `{os_type}` |")
    md.append(f"| Fase alcanzada | `{phase}` |")
    md.append(f"| ¿Sistema comprometido? | {'✅ **SÍ**' if compromised else '❌ no'} |")
    md.append(f"| Puertos abiertos | **{len(ports)}** |")
    md.append(f"| Credenciales/usuarios obtenidos | **{len(creds)}** |")
    if last_session_id:
        md.append(f"| Sesión Meterpreter abierta | id=`{last_session_id}` |")
    if lhost:
        md.append(f"| LHOST (executor en red lab) | `{lhost}` |")
    md.append("")

    # ============== Reconocimiento ==============
    md.append("## Reconocimiento")
    md.append("")
    if ports:
        md.append(f"Se detectaron **{len(ports)}** puertos abiertos en `{target}`:")
        md.append("")
        md.append("```")
        md.append(", ".join(str(p) for p in sorted(ports)))
        md.append("```")
    else:
        md.append("_No se detectaron puertos abiertos._")
    md.append("")

    # ============== Explotación ==============
    md.append("## Explotación")
    md.append("")
    if compromised:
        md.append(f"El sistema fue comprometido (`is_compromised = True`).")
        if last_session_id:
            md.append("")
            md.append(f"- Sesión activa en msfrpcd: **id=`{last_session_id}`**")
            md.append(f"- Esta sesión sobrevivió a la transición a post-explotación")
            md.append(f"  gracias a la console persistente RPC.")
    else:
        md.append("_El sistema NO fue comprometido en este run._")
        md.append("")
        md.append("Revisa los logs en `data/logs/exploit_attempts/` para ver qué falló.")
    md.append("")

    # ============== Credenciales (desglose por tipo) ==============
    md.append("## Credenciales y usuarios descubiertos")
    md.append("")
    if creds:
        buckets = _bucket_credentials(creds)
        types_order = ["passwd", "shadow", "ntlm", "otros"]

        md.append(f"Total: **{len(creds)}** entradas, desglosadas:")
        md.append("")
        md.append("| Tipo | Cantidad |")
        md.append("|---|---|")
        for t in types_order:
            if t in buckets:
                md.append(f"| `{t}` | {len(buckets[t])} |")
        md.append("")

        for t in types_order:
            if t not in buckets:
                continue
            md.append(f"### `{t}` ({len(buckets[t])} entradas)")
            md.append("")
            md.append("```")
            for c in buckets[t]:
                md.append(c)
            md.append("```")
            md.append("")

        # Notas accionables sobre los hashes
        if "shadow" in buckets:
            md.append("> 💡 Los hashes `shadow` se pueden crackear con "
                      "`hashcat -m 500 hashes.txt rockyou.txt` (MD5-crypt) "
                      "o `john --format=md5crypt`.")
            md.append("")
        if "ntlm" in buckets:
            md.append("> 💡 Los hashes `ntlm` se pueden crackear con "
                      "`hashcat -m 1000 hashes.txt rockyou.txt` o pasar "
                      "directamente con `pth-winexe` / `crackmapexec`.")
            md.append("")
    else:
        md.append("_No se obtuvieron credenciales._")
    md.append("")

    # ============== Logs de exploits ==============
    md.append("## Intentos de explotación registrados")
    md.append("")
    if os.path.isdir(_EXPLOIT_LOG_DIR):
        files = sorted(os.listdir(_EXPLOIT_LOG_DIR))
        if files:
            md.append(f"Se han registrado **{len(files)}** ejecuciones msfconsole "
                      f"con sus outputs completos en `{_EXPLOIT_LOG_DIR}/`:")
            md.append("")
            # Mostrar los más recientes primero, máximo 30 entries para no inflar
            recent = files[-30:] if len(files) > 30 else files
            for f in reversed(recent):
                md.append(f"- `{f}`")
            if len(files) > 30:
                md.append(f"- _... y {len(files) - 30} más antiguos_")
        else:
            md.append("_Sin intentos registrados._")
    else:
        md.append("_Carpeta de logs no disponible._")
    md.append("")

    # ============== Pie ==============
    md.append("---")
    md.append("")
    md.append(
        "_Informe generado automáticamente por **AIPen** "
        "(LangGraph + qwen2.5:3b local + catálogo YAML + RAG FAISS + msfrpcd)._"
    )
    md.append("")

    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(md))
    except OSError as e:
        print(f"[report] Error escribiendo {path}: {e}")
        return ""

    return path
