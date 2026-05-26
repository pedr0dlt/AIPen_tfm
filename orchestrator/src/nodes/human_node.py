from __future__ import annotations

import json
from typing import Any

from src.state import PentestState
from src.cli.renderer import (
    render_turn_panel,
    render_state_dump,
    render_agent_info,
    render_playbook,
    render_last_output,
    help_block,
)


def _last_thought(state: PentestState) -> str:
    msgs = state.get("messages", []) or []
    for m in reversed(msgs):
        if m.get("role") != "assistant":
            continue
        content = (m.get("content") or "").strip()
        if not content:
            continue
        try:
            obj = json.loads(content)
            if isinstance(obj, dict):
                return str(obj.get("thought", "") or "")
        except json.JSONDecodeError:
            return ""
        return ""
    return ""


def _build_proposed(state: PentestState) -> dict[str, Any]:
    thought = _last_thought(state)
    args = state.get("next_tool_args", "") or ""
    msgs = state.get("messages", []) or []
    exploit_id = ""
    is_fin = args.upper() == "FIN"
    for m in reversed(msgs):
        if m.get("role") != "assistant":
            continue
        try:
            obj = json.loads(m.get("content", "") or "")
            if isinstance(obj, dict) and obj.get("action") == "exploit":
                exploit_id = str(obj.get("exploit_id", "") or "")
        except Exception:
            pass
        break
    if is_fin:
        action = "FIN (avance de fase)"
    elif exploit_id:
        action = "exploit"
    else:
        action = "shell"
    return {
        "thought": thought,
        "action": action,
        "exploit_id": exploit_id,
        "args": args,
    }


def human_approval_node(state: PentestState):
    proposed = _build_proposed(state)

    last_out = state.get("last_command_output", "") or ""
    if last_out:
        print(render_last_output(last_out))

    is_retry = (state.get("next_tool") or "") == "retry"
    if is_retry:
        sys_msg = ""
        for m in reversed(state.get("messages", []) or []):
            if m.get("role") == "user":
                c = (m.get("content") or "").strip()
                if c.startswith("[SISTEMA]"):
                    sys_msg = c
                    break
        retries = state.get("format_retries", 0)
        print("\n  \033[33m[!] El parser ha rechazado la última respuesta del LLM.\033[0m")
        print(f"  retries semánticos acumulados: {retries}")
        if sys_msg:
            for line in sys_msg.splitlines():
                print(f"  | {line}")
        print("  → Enter = deja al LLM reintentar | "
              "m <texto> = corrígelo tú | q = abandonar.\n")

    print(render_turn_panel(state, proposed=proposed,
                            turn=state.get("commands_in_phase", 0) + 1))
    print(help_block())

    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[CLI] Interrupción — saliendo con FIN.")
            return {
                "human_decision": "quit",
                "next_tool": "executor",
                "next_tool_args": "FIN",
            }

        low = raw.lower()

        if low in ("/state", "state"):
            print(render_state_dump(state))
            continue
        if low in ("/agent", "agent"):
            print(render_agent_info(state))
            continue
        if low in ("/playbook", "playbook"):
            print(render_playbook(state))
            continue
        if low in ("/help", "help", "?"):
            print(help_block())
            continue

        if raw == "" or low in ("e", "enter", "y", "yes", "ejecutar"):
            print("[CLI] Ejecutando acción propuesta.")
            return {"human_decision": "execute"}

        if low in ("s", "/skip", "skip", "n", "no"):
            print("[CLI] Saltando esta acción.")
            return {
                "human_decision": "skip",
                "next_tool": "",
                "next_tool_args": "",
                "format_retries": 0,
                "messages": [{
                    "role": "user",
                    "content": (
                        "[OPERADOR] He saltado tu última propuesta. "
                        "Razona y propone la siguiente acción."
                    ),
                }],
            }

        if low in ("a", "/auto", "auto"):
            print("[CLI] AUTO desde aquí — el resto del run corre sin guiado.")
            return {
                "human_decision": "auto",
                "interactive_mode": False,
            }

        if low in ("/next", "next", "n>", ">>"):
            print("[CLI] Avance manual de fase.")
            return {
                "human_decision": "advance",
                "next_tool": "",
                "next_tool_args": "",
            }

        if low in ("/output", "/out", "out", "output"):
            if last_out:
                print(render_last_output(last_out, full=True))
            else:
                print("[CLI] No hay salida previa todavía.")
            continue

        # /cred user:pass            -> login: ssh://user:pass@<target>:22
        # /cred ssh://user:pass@host -> tal cual
        # /cred user:pass@host[:port][svc=ssh]
        if low.startswith("/cred ") or low.startswith("cred "):
            spec = raw.split(None, 1)[1].strip() if " " in raw else ""
            if not spec or ":" not in spec:
                print("[CLI] Uso: /cred USER:PASS  o  /cred ssh://USER:PASS@HOST:PORT")
                continue
            target = state.get("target_ip", "") or "target"
            if "://" in spec:
                cred_line = f"login: {spec}"
            elif "@" in spec:
                # user:pass@host[:port]
                cred_line = f"login: ssh://{spec}:22" if ":" not in spec.rsplit("@", 1)[1] else f"login: ssh://{spec}"
            else:
                cred_line = f"login: ssh://{spec}@{target}:22"
            print(f"[CLI] Guardando credencial manual: {cred_line}")
            return {
                "human_decision": "inject",
                "next_tool": "",
                "next_tool_args": "",
                "format_retries": 0,
                "acquired_credentials": [cred_line],
                "messages": [{
                    "role": "user",
                    "content": (
                        f"[OPERADOR] He añadido al estado la credencial: "
                        f"{cred_line}. Úsala en tus próximas acciones."
                    ),
                }],
            }

        if low in ("q", "/quit", "quit", "exit"):
            print("[CLI] Terminando run con FIN.")
            return {
                "human_decision": "quit",
                "next_tool": "executor",
                "next_tool_args": "FIN",
            }

        if low.startswith("m ") or raw.startswith("/inject "):
            text = raw[2:] if low.startswith("m ") else raw[len("/inject "):]
            text = text.strip()
            if not text:
                print("[CLI] Mensaje vacío, ignorado.")
                continue
            print(f"[CLI] Inyectando mensaje al LLM: {text[:120]}")
            return {
                "human_decision": "inject",
                "next_tool": "",
                "next_tool_args": "",
                "format_retries": 0,
                "messages": [{
                    "role": "user",
                    "content": f"[OPERADOR] {text}",
                }],
            }

        if not raw.startswith("/") and len(raw.split()) >= 2:
            print(f"[CLI] (sin 'm ' delante) → inyectando como mensaje: {raw[:120]}")
            return {
                "human_decision": "inject",
                "next_tool": "",
                "next_tool_args": "",
                "format_retries": 0,
                "messages": [{
                    "role": "user",
                    "content": f"[OPERADOR] {raw}",
                }],
            }
        print(f"[!] Comando no reconocido: {raw!r}. "
              f"¿Querías inyectar? Usa 'm <texto>'. Usa /help para ver opciones.")
