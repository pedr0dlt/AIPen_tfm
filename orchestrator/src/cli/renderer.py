from __future__ import annotations

import json
import os
import sys
from typing import Any


def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


_C_RESET = "\033[0m"
_C_DIM = "\033[2m"
_C_BOLD = "\033[1m"
_C_CYAN = "\033[36m"
_C_YELLOW = "\033[33m"
_C_GREEN = "\033[32m"
_C_RED = "\033[31m"
_C_MAGENTA = "\033[35m"


def _c(text: str, color: str) -> str:
    if not _supports_color():
        return text
    return f"{color}{text}{_C_RESET}"


def banner() -> str:
    return (
        "\n"
        + _c("╔══════════════════════════════════════════════════════════════╗", _C_CYAN) + "\n"
        + _c("║              AIPen — Modo CLI guiado (F7)                    ║", _C_CYAN) + "\n"
        + _c("║   Aprobación humana antes de cada acción del agente.         ║", _C_CYAN) + "\n"
        + _c("╚══════════════════════════════════════════════════════════════╝", _C_CYAN) + "\n"
    )


def help_block() -> str:
    return (
        "  " + _c("[Enter]", _C_GREEN) + "  ejecutar la acción propuesta\n"
        "  " + _c("[s]", _C_YELLOW) + "       saltar — pide al LLM la siguiente\n"
        "  " + _c("[m <txt>]", _C_YELLOW) + " inyectar mensaje al LLM (no ejecuta)\n"
        "  " + _c("[a]", _C_MAGENTA) + "       AUTO desde aquí (desactiva guiado)\n"
        "  " + _c("[q]", _C_RED) + "       quit — termina con FIN limpio\n"
        "  " + _c("/next", _C_CYAN) + "     avance MANUAL de fase (recon→exploit→post→done)\n"
        "  " + _c("/output", _C_CYAN) + "   muestra la salida COMPLETA del último comando\n"
        "  " + _c("/cred USER:PASS", _C_CYAN) + "  guarda credencial manual al estado\n"
        "  Slash: /agent  /inject <txt>  /state  /playbook  /skip  /auto  /quit\n"
    )


def _shorten(s: str | None, n: int = 240) -> str:
    s = (s or "").strip().replace("\n", " ")
    return s if len(s) <= n else s[: n - 3] + "..."


def render_turn_panel(
    state: dict[str, Any],
    proposed: dict[str, Any] | None = None,
    turn: int | None = None,
) -> str:
    """Genera el panel de un turno: contexto + acción propuesta."""
    phase = state.get("current_phase", "?")
    os_type = state.get("os_type", "?")
    ports = state.get("discovered_ports", []) or []
    creds = state.get("acquired_credentials", []) or []
    sess_id = state.get("last_session_id", 0) or 0

    ports_short = ",".join(str(p) for p in ports[:12])
    if len(ports) > 12:
        ports_short += f",…(+{len(ports) - 12})"

    head = "─" * 64
    lines: list[str] = []
    lines.append(_c(head, _C_DIM))
    turn_tag = f"Turno {turn}" if turn is not None else "Turno —"
    lines.append(
        _c(f"[{turn_tag}]", _C_BOLD)
        + f"  fase={_c(phase, _C_CYAN)}  os={os_type}  "
        + f"sesión={sess_id or '-'}  creds={len(creds)}"
    )
    lines.append(f"  puertos: {ports_short or '-'}")
    lines.append("")

    if proposed is None:
        proposed = {
            "thought": "",
            "action": state.get("next_tool", "") or "?",
            "args": state.get("next_tool_args", "") or "",
        }

    thought = _shorten(proposed.get("thought"))
    if thought:
        lines.append("  " + _c("Thought ", _C_DIM) + ": " + thought)
    lines.append("  " + _c("Action  ", _C_DIM) + ": " + _c(str(proposed.get("action", "?")), _C_YELLOW))
    if proposed.get("exploit_id"):
        lines.append("  " + _c("Exploit ", _C_DIM) + ": " + str(proposed["exploit_id"]))
    args = proposed.get("args") or proposed.get("command") or ""
    if args:
        lines.append("  " + _c("Comando ", _C_DIM) + ": " + _shorten(args, 280))
    lines.append(_c(head, _C_DIM))
    return "\n".join(lines)


def render_state_dump(state: dict[str, Any]) -> str:
    keys = [
        "target_ip", "current_phase", "os_type", "is_compromised",
        "discovered_ports", "acquired_credentials", "last_session_id",
        "commands_in_phase", "executed_commands", "format_retries",
        "interactive_mode",
    ]
    snapshot = {k: state.get(k) for k in keys}
    return _c("── /state ──", _C_DIM) + "\n" + json.dumps(snapshot, indent=2, ensure_ascii=False)


def render_agent_info(state: dict[str, Any]) -> str:
    from src.catalog import applicable_entries

    phase = state.get("current_phase", "?")
    ports = state.get("discovered_ports", []) or []
    os_type = state.get("os_type", "unknown")
    entries = applicable_entries(ports, os_type) if phase == "exploitation" else []
    ids = [e["id"] for e in entries]
    lines = [
        _c("── /agent ──", _C_DIM),
        f"  fase           : {phase}",
        f"  os_type        : {os_type}",
        f"  ports          : {ports}",
        f"  catálogo aplic.: {ids or '(vacío para esta fase)'}",
        f"  interactive    : {state.get('interactive_mode', False)}",
    ]
    return "\n".join(lines)


def render_last_output(text: str, full: bool = False, max_lines: int = 25) -> str:
    head = _c("── Salida del comando anterior ──", _C_DIM)
    if not text:
        return head + "\n  (vacío)"

    lines = text.splitlines() or [text]
    total = len(lines)
    if not full and total > max_lines:
        shown = lines[-max_lines:]
        trimmed = f"  …({total - max_lines} líneas previas omitidas — /output para ver todo)\n"
    else:
        shown = lines
        trimmed = ""

    body = "\n".join("  " + ln for ln in shown)
    return head + "\n" + trimmed + body + "\n" + _c("──────────────────────────────────", _C_DIM)


def render_playbook(state: dict[str, Any]) -> str:
    try:
        from src.nodes.knowledge_node import load_playbook
    except Exception as e:  # pragma: no cover
        return f"[!] No se pudo cargar knowledge_node: {e}"

    ctx = load_playbook(
        phase=state.get("current_phase", "recon"),
        os_type=state.get("os_type", "unknown"),
        open_ports=state.get("discovered_ports", []) or [],
        last_output=state.get("last_command_output", "") or "",
    )
    head = _c("── /playbook ──", _C_DIM)
    body = ctx if ctx else "(sin playbook recuperado para este contexto)"
    return f"{head}\n{body}"
