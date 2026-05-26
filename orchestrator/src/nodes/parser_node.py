from __future__ import annotations

import json
import re
import shlex
from src.state import PentestState
from src.catalog import lookup, render_msfconsole, applicable_ids


_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


def _sanitize_shell_command(cmd: str) -> str:
    cleaned = (cmd or "").strip()
    if not cleaned:
        return cleaned

    # '}' final colgante (otro fallo típico cuando duplica JSON)
    while cleaned.endswith("}"):
        cleaned = cleaned[:-1].rstrip()

    try:
        tokens = shlex.split(cleaned)
        # Caso especial: todo entrecomillado → 1 token con el comando entero.
        if (
            len(tokens) == 1
            and len(cleaned) >= 2
            and cleaned[0] in ("'", '"')
            and cleaned[-1] == cleaned[0]
        ):
            return cleaned[1:-1].strip()
        return cleaned  # bien formado, no tocamos
    except ValueError:
        pass  # comilla sin cerrar

    # Hasta 3 capas
    original = cleaned
    for _ in range(3):
        # comilla solo al principio
        if cleaned and cleaned[0] in ("'", '"'):
            test = cleaned[1:].strip()
            try:
                shlex.split(test)
                print(f"[~] parser: pelada comilla inicial → {test[:90]}")
                return test
            except ValueError:
                pass
        # comilla solo al final
        if cleaned and cleaned[-1] in ("'", '"'):
            test = cleaned[:-1].strip()
            try:
                shlex.split(test)
                print(f"[~] parser: pelada comilla final → {test[:90]}")
                return test
            except ValueError:
                pass
        # comillas en ambos extremos
        if (
            len(cleaned) >= 2
            and cleaned[0] in ("'", '"')
            and cleaned[-1] in ("'", '"')
        ):
            cleaned = cleaned[1:-1].strip()
            try:
                shlex.split(cleaned)
                print(f"[~] parser: peladas comillas envolventes → {cleaned[:90]}")
                return cleaned
            except ValueError:
                continue
        break

    if cleaned != original:
        print(f"[!] parser: comando sigue mal formado tras sanear: {cleaned[:90]}")
    return cleaned


def _try_parse_json(text: str) -> dict | None:
    if not text:
        return None
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        pass
    m = _JSON_OBJECT_RE.search(text)
    if m:
        try:
            obj = json.loads(m.group(0))
            return obj if isinstance(obj, dict) else None
        except json.JSONDecodeError:
            return None
    return None


def parser_node(state: PentestState):
    print("--- [Nodo Parser] Extrayendo acción JSON... ---")
    last_message = state["messages"][-1]["content"]
    parsed = _try_parse_json(last_message)

    if parsed is None:
        print("[-] No se pudo parsear JSON en la respuesta del LLM.")
        return {
            "next_tool": "none",
            "next_tool_args": "",
        }

    action = str(parsed.get("action", "")).lower()
    thought = parsed.get("thought", "")
    if thought:
        print(f"[*] Thought: {thought[:200]}")

    if action == "fin":
        print("[*] Acción: FIN")
        return {
            "next_tool": "executor",     
            "next_tool_args": "FIN",
        }

    if action == "shell":
        cmd = (parsed.get("command") or "").strip()
        if not cmd:
            return {
                "next_tool": "retry",
                "next_tool_args": "",
                "format_retries": state.get("format_retries", 0) + 1,
                "messages": [{
                    "role": "user",
                    "content": (
                        "[SISTEMA] La acción 'shell' requiere un campo 'command' "
                        "no vacío. Reintenta con la estructura correcta."
                    )
                }]
            }
        sanitized = _sanitize_shell_command(cmd)
        if sanitized != cmd:
            print(f"[*] Acción shell (saneada): {sanitized[:120]}")
        else:
            print(f"[*] Acción shell: {cmd[:120]}")
        return {
            "next_tool": "executor",
            "next_tool_args": sanitized,
        }

    if action == "exploit":
        phase = state.get("current_phase", "")
        if phase == "post-exploitation":
            exploit_id = (parsed.get("exploit_id") or "").strip()
            creds = state.get("acquired_credentials", []) or []
            last_sid = state.get("last_session_id", 0) or 0
            if last_sid:
                hint = (
                    f"Tienes sesión Meterpreter id={last_sid} en msfrpcd. "
                    f"Usa: msfconsole -q -x \"sessions -i {last_sid} -c "
                    f"'hashdump'\""
                )
            elif creds:
                hint = (
                    f"Tienes {len(creds)} credenciales válidas en estado. "
                    f"Usa sshpass+ssh, p.ej.: "
                    f'{{"action":"shell","command":"sshpass -pPASS ssh -o '
                    f"StrictHostKeyChecking=no USER@{state.get('target_ip', '')} "
                    f'sudo -l"}}'
                )
            else:
                hint = (
                    "No tienes creds ni sesión. Usa `action:shell` con un "
                    "comando que ya hayas validado en explotación."
                )
            print(f"[!] action='exploit' bloqueado en post-exploitation "
                  f"(intentó '{exploit_id}')")
            return {
                "next_tool": "retry",
                "next_tool_args": "",
                "format_retries": state.get("format_retries", 0) + 1,
                "messages": [{
                    "role": "user",
                    "content": (
                        f"[SISTEMA] En POST-EXPLOTACIÓN está PROHIBIDO "
                        f"`action:exploit`. El catálogo MSF no se usa aquí. "
                        f"{hint}"
                    )
                }]
            }

        exploit_id = (parsed.get("exploit_id") or "").strip()
        entry = lookup(exploit_id)
        if entry is None:
            valid = applicable_ids(
                state.get("discovered_ports", []),
                state.get("os_type", "unknown"),
            )
            print(f"[!] exploit_id desconocido: '{exploit_id}'. Válidos: {valid}")
            return {
                "next_tool": "retry",
                "next_tool_args": "",
                "format_retries": state.get("format_retries", 0) + 1,
                "messages": [{
                    "role": "user",
                    "content": (
                        f"[SISTEMA] El exploit_id '{exploit_id}' no existe en el "
                        f"catálogo. Usa uno de estos ids válidos para los puertos "
                        f"detectados: {valid}. Si la lista está vacía, completa el "
                        f"recon primero con un comando shell tipo nmap."
                    )
                }]
            }

        target = state["target_ip"]
        lhost = state.get("lhost", "") or "TU_LHOST"
        rendered = render_msfconsole(entry, target=target, lhost=lhost)
        print(f"[*] Acción exploit: {exploit_id}")
        print(f"    └─ render: {rendered[:140]}{'...' if len(rendered) > 140 else ''}")
        return {
            "next_tool": "executor",
            "next_tool_args": rendered,
        }

    print(f"[-] Acción desconocida: {action!r}")
    return {
        "next_tool": "retry",
        "next_tool_args": "",
        "format_retries": state.get("format_retries", 0) + 1,
        "messages": [{
            "role": "user",
            "content": (
                f"[SISTEMA] action='{action}' no es válida. Usa una de: "
                f"'shell', 'exploit', 'FIN'."
            )
        }]
    }
