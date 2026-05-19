from __future__ import annotations

import os
import re
from datetime import datetime
import requests
from src.state import PentestState
from src.msf_client import execute_via_console as msf_execute_via_console

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


_COMPROMISE_PATTERNS = (
    r"meterpreter\s*>",
    r"meterpreter session\s+\d+\s+opened",
    r"command shell session\s+\d+\s+opened",
    r"shell session\s+\d+\s+opened",
    r"session\s+\d+\s+opened",
    r"\buid=\d+",                     
    r"server username:\s*\S",         
    r"backdoor has been spawned",
    r"successfully created.*session",
)

# /etc/passwd
_PASSWD_LINE_RE = re.compile(
    r"^([a-zA-Z0-9_.\-]{1,32}):x?:(\d+):(\d+):[^:]*:[^:]*:.+$",
    re.MULTILINE,
)

# /etc/shadow
_SHADOW_HASH_RE = re.compile(
    r"^([a-zA-Z0-9_.\-]{1,32}):(\$[16y5][a-z]?\$[^:\s]+):",
    re.MULTILINE,
)

# NTLM 
_NTLM_HASH_RE = re.compile(
    r"^([a-zA-Z0-9_.\-]{1,32}):\d+:([a-f0-9]{32}):([a-f0-9]{32}):::",
    re.MULTILINE | re.IGNORECASE,
)

# True si hay shell remota
def _detect_compromise(output: str) -> bool:
    for pat in _COMPROMISE_PATTERNS:
        if re.search(pat, output, re.IGNORECASE):
            return True
    return False


def _extract_credentials(output: str) -> list[str]:
    found: list[str] = []

    for m in _PASSWD_LINE_RE.finditer(output):
        user, uid, gid = m.group(1), m.group(2), m.group(3)
        try:
            uid_int = int(uid)
        except ValueError:
            continue
        if user == "root" or uid_int >= 1000 or uid_int == 0:
            found.append(f"passwd: {user} (uid={uid}, gid={gid})")

    for m in _SHADOW_HASH_RE.finditer(output):
        user, h = m.group(1), m.group(2)
        h_short = h if len(h) <= 50 else h[:47] + "..."
        found.append(f"shadow: {user}:{h_short}")

    for m in _NTLM_HASH_RE.finditer(output):
        user, _lm, ntlm = m.group(1), m.group(2), m.group(3)
        found.append(f"ntlm: {user}:{ntlm}")

    seen: set[str] = set()
    unique: list[str] = []
    for f in found:
        if f not in seen:
            seen.add(f)
            unique.append(f)
    return unique


# Nodo principal
def tool_node(state: PentestState):
    comando = state.get("next_tool_args", "")

    if not comando or comando.upper() == "FIN":
        return {"last_command_output": "Ejecución finalizada por el agente."}

    stripped = comando.lstrip()
    if stripped.lower().startswith("sessions "):
        if not stripped.rstrip().endswith("exit -y"):
            stripped = stripped.rstrip().rstrip(";") + "; exit -y"
        comando = f'msfconsole -q -x "{stripped}"'
        print(f"[~] Auto-wrap: comando 'sessions ...' envuelto en msfconsole -q -x")

    # B1 — Anti-duplicado por fase: si el LLM repite EXACTAMENTE un comando
    # ya ejecutado en esta fase (post-auto-wrap), NO lo volvemos a lanzar.
    # Devolvemos feedback sintético que fuerza al LLM a probar otra cosa
    # o a decir FIN. `executed_commands` se resetea en cada transición de fase.
    cmd_norm = " ".join(comando.strip().lower().split())
    executed = state.get("executed_commands", []) or []
    if cmd_norm in executed:
        synthetic = (
            f"[BLOQUEADO POR EL AGENTE] El comando «{comando[:120]}» ya se "
            f"ejecutó en esta fase y produjo el mismo resultado. NO repitas. "
            f"Prueba otra acción DIFERENTE — ejemplos meterpreter: hashdump, "
            f"sysinfo, ls /home, arp, ifconfig, cat /etc/shadow, getuid. "
            f'Si ya no queda nada útil que extraer, responde {{"action":"FIN"}}.'
        )
        print(f"[!] Comando duplicado bloqueado: {comando[:80]}...")
        return {
            "last_command_output": synthetic,
            "messages": [{"role": "user", "content": synthetic}],
            "next_tool": "",
            "next_tool_args": "",
        }

    # F4 — Guard de fase: en post-explotación está PROHIBIDO re-explotar.
    # El LLM tiende a volver a tirar `use exploit/...` en lugar de usar la
    # sesión ya abierta. Esta guard es del mismo tipo que B1 (anti-dup) y
    # F-V1 (validador msf): protege contra una clase de error específico.
    phase = state.get("current_phase", "")
    if phase == "post-exploitation" and "use exploit/" in comando.lower():
        last_sid = state.get("last_session_id", 0) or 1
        synthetic = (
            f"[BLOQUEADO POR EL AGENTE] En POST-EXPLOTACIÓN está prohibido "
            f"`use exploit/...`. La sesión id={last_sid} ya está activa en "
            f"msfrpcd; debes trabajar SOBRE ella, no re-explotar.\n"
            f"Emite algo así:\n"
            f'{{"action":"shell","command":"sessions -i {last_sid} -c '
            f"'hashdump'\"}}\n"
            f"Comandos meterpreter útiles: getuid, sysinfo, hashdump, "
            f"cat /etc/shadow, ls /home, arp, ifconfig.\n"
            f'Cuando hayas extraído lo posible, responde {{"action":"FIN"}}.'
        )
        print(f"[!] Bloqueado intento de re-exploit en post-exploitation: "
              f"{comando[:80]}...")
        return {
            "last_command_output": synthetic,
            "messages": [{"role": "user", "content": synthetic}],
            "next_tool": "",
            "next_tool_args": "",
        }

    print(f"--- [Nodo Tool] Ejecutando remotamente: {comando[:140]}{'...' if len(comando) > 140 else ''} ---")

    rpc_output = None
    if "msfconsole" in comando.lower():
        rpc_output = msf_execute_via_console(comando, total_timeout=180)
        if rpc_output is not None:
            print(f"[*] Ejecutado vía msfrpcd (console persistente, {len(rpc_output)} chars)")

    if rpc_output is not None:
        output = f"[STDOUT]\n{rpc_output}\n[STDERR]\n"
    else:
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

    compromised_now = _detect_compromise(output)
    new_creds = _extract_credentials(output)

    if not compromised_now and new_creds:
        has_proof_of_rce = any(
            c.startswith(("shadow:", "ntlm:")) for c in new_creds
        )
        if has_proof_of_rce:
            compromised_now = True
            print("[+] Compromiso inferido por hashes shadow/ntlm extraídos")

    if new_creds:
        by_type: dict[str, list[str]] = {}
        for c in new_creds:
            prefix = c.split(":", 1)[0] if ":" in c else "otro"
            by_type.setdefault(prefix, []).append(c)
        types_summary = ", ".join(f"{t}={len(items)}" for t, items in by_type.items())
        print(f"[+] Credenciales extraídas: {len(new_creds)}  ({types_summary})")
        for tname, items in by_type.items():
            for c in items[:2]:
                print(f"    · {c}")
            if len(items) > 2:
                print(f"    · ... y {len(items) - 2} más de tipo '{tname}'")

    # B1 — añadir el comando ejecutado al registro de la fase para detectar
    # repeticiones futuras. `executed_commands` se resetea en cada transición.
    new_executed = list(executed) + [cmd_norm]

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
        "executed_commands": new_executed,
    }

    if state.get("os_type", "unknown") == "unknown":
        detected = _detect_os(output)
        if detected:
            print(f"[*] OS detectado: {detected.upper()}")
            updates["os_type"] = detected

    if compromised_now and not state.get("is_compromised", False):
        print("[+] ¡Sistema COMPROMETIDO! (detectado en output)")
        updates["is_compromised"] = True

    if new_creds:
        existing = set(state.get("acquired_credentials", []) or [])
        truly_new = [c for c in new_creds if c not in existing]
        if truly_new:
            updates["acquired_credentials"] = truly_new

    return updates
