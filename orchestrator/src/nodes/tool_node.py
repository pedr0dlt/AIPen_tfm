from __future__ import annotations

import os
import re
from datetime import datetime
import requests
from src.state import PentestState

EXECUTOR_HOST = os.getenv("EXECUTOR_HOST", "http://localhost:8000")

# Parámetros
_EXPLOIT_LOG_DIR = "/logs/exploit_attempts"
_MAX_OUTPUT_CHARS_FOR_LLM = 1500
_KEYWORDS_KEEP = (
    "open", "vulnerable", "shell", "session", "meterpreter",
    "credential", "password", "hash", "root", "admin", "user=",
    "uid=", "gid=", "exploit", "rce", "msf", "cve-",
    "succeed", "failed", "found", "smb", "http",
)


def _smart_truncate(output: str) -> str:
    if len(output) <= _MAX_OUTPUT_CHARS_FOR_LLM:
        return output

    lines = output.splitlines()
    keep_head = lines[:6]
    keep_tail = lines[-6:]
    keep_middle = [
        ln for ln in lines[6:-6]
        if any(kw in ln.lower() for kw in _KEYWORDS_KEEP)
    ]

    pieces = (
        keep_head
        + (["...[líneas relevantes]..."] if keep_middle else [])
        + keep_middle
        + ["...[fin output truncado]..."]
        + keep_tail
    )
    truncated = "\n".join(pieces)
    if len(truncated) > _MAX_OUTPUT_CHARS_FOR_LLM:
        truncated = truncated[:_MAX_OUTPUT_CHARS_FOR_LLM] + "\n...[corte duro]..."
    return truncated


def _dump_exploit_output(command: str, output: str) -> None:
    if "msfconsole" not in command.lower():
        return
    try:
        os.makedirs(_EXPLOIT_LOG_DIR, exist_ok=True)
        m = re.search(
            r"use\s+((?:exploit|auxiliary|post)/[a-zA-Z0-9_./\-]+)",
            command,
        )
        module_safe = m.group(1).replace("/", "_") if m else "raw"
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(_EXPLOIT_LOG_DIR, f"{ts}_{module_safe}.log")
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# Timestamp (UTC):\n{ts}\n\n")
            f.write(f"# Command:\n{command}\n\n")
            f.write(f"# Output ({len(output)} chars):\n{output}\n")
        print(f"[*] Log de msfconsole guardado en {path}")
    except Exception as e:
        print(f"[!] No se pudo guardar log de msfconsole: {e}")


_OS_PATTERNS = {
    "windows": [
        r"(?i)OS details:.*windows",
        r"(?i)Running:.*windows",
        r"(?i)OS:.*windows",
        r"(?i)cpe:/o:microsoft:windows",
        r"(?i)microsoft windows",
        r"ttl[= ]+12[0-9]\b",   # TTL ~128 = Windows
    ],
    "linux": [
        r"(?i)OS details:.*linux",
        r"(?i)Running:.*linux",
        r"(?i)OS:.*linux",
        r"(?i)cpe:/o:linux",
        r"(?i)\bunix\b",
        r"ttl[= ]+6[0-4]\b",    # TTL ~64 = Linux/Unix
    ],
}


def _detect_os(output: str) -> str | None:
    for os_name, patterns in _OS_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, output):
                return os_name
    return None


def _extract_ports(output: str) -> list[int]:
    ports: list[int] = []
    for line in output.splitlines():
        m = re.match(r"^(\d+)/(tcp|udp)\s+open\s+", line)
        if m:
            ports.append(int(m.group(1)))
    return ports


# Nodo principal
def tool_node(state: PentestState):
    comando = state.get("next_tool_args", "")

    if not comando or comando.upper() == "FIN":
        return {"last_command_output": "Ejecución finalizada por el agente."}

    print(f"--- [Nodo Tool] Ejecutando remotamente: {comando[:140]}{'...' if len(comando) > 140 else ''} ---")

    try:
        response = requests.post(
            f"{EXECUTOR_HOST}/execute",
            json={"command": comando, "timeout": 300},
            timeout=310
        )
        response.raise_for_status()
        result = response.json()
        output = f"[STDOUT]\n{result['stdout']}\n[STDERR]\n{result['stderr']}"
        print(f"[*] Salida recibida ({len(output)} caracteres)")
    except Exception as e:
        output = f"Error al intentar ejecutar la herramienta en Kali: {str(e)}"
        print(f"[-] {output}")

    _dump_exploit_output(comando, output)

    current_ports = state.get("discovered_ports", []) or []
    new_ports = _extract_ports(output)
    updated_ports = sorted(set(current_ports + new_ports))
    if new_ports:
        diff = sorted(set(new_ports) - set(current_ports))
        if diff:
            print(f"[*] Puertos detectados: {diff}")

    output_for_llm = _smart_truncate(output)
    if len(output_for_llm) < len(output):
        print(f"[*] Output truncado para el LLM: {len(output)} → {len(output_for_llm)} chars")

    updates = {
        "last_command_output": output,
        "messages": [{
            "role": "user",
            "content": f"Resultado de tu comando '{comando[:80]}{'...' if len(comando) > 80 else ''}':\n{output_for_llm}"
        }],
        "next_tool": "",
        "next_tool_args": "",
        "commands_in_phase": state.get("commands_in_phase", 0) + 1,
        "discovered_ports": updated_ports,
    }

    if state.get("os_type", "unknown") == "unknown":
        detected = _detect_os(output)
        if detected:
            print(f"[*] OS detectado: {detected.upper()}")
            updates["os_type"] = detected

    return updates
