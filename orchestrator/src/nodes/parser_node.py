from __future__ import annotations

import json
import re
from src.state import PentestState
from src.catalog import lookup, render_msfconsole, applicable_ids


_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


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
                "messages": [{
                    "role": "user",
                    "content": (
                        "[SISTEMA] La acción 'shell' requiere un campo 'command' "
                        "no vacío. Reintenta con la estructura correcta."
                    )
                }]
            }
        print(f"[*] Acción shell: {cmd[:120]}")
        return {
            "next_tool": "executor",
            "next_tool_args": cmd,
        }

    if action == "exploit":
        exploit_id = (parsed.get("exploit_id") or "").strip()
        entry = lookup(exploit_id)
        if entry is None:
            # exploit_id no existe en el catálogo → feedback sintético al LLM
            valid = applicable_ids(
                state.get("discovered_ports", []),
                state.get("os_type", "unknown"),
            )
            print(f"[!] exploit_id desconocido: '{exploit_id}'. Válidos: {valid}")
            return {
                "next_tool": "retry",
                "next_tool_args": "",
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
        "messages": [{
            "role": "user",
            "content": (
                f"[SISTEMA] action='{action}' no es válida. Usa una de: "
                f"'shell', 'exploit', 'FIN'."
            )
        }]
    }
