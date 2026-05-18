from __future__ import annotations

from src.state import PentestState


# Orden de las fases
_PHASE_ORDER = ["recon", "exploitation", "post-exploitation", "done"]


def _next_phase(current: str) -> str:
    try:
        idx = _PHASE_ORDER.index(current)
    except ValueError:
        return "done"
    if idx + 1 >= len(_PHASE_ORDER):
        return "done"
    return _PHASE_ORDER[idx + 1]


def _print_phase_summary(phase: str, state: PentestState) -> None:
    ports = state.get("discovered_ports", []) or []
    creds = state.get("acquired_credentials", []) or []
    os_type = state.get("os_type", "unknown")
    cmds = state.get("commands_in_phase", 0)
    compromised = state.get("is_compromised", False)

    print("\n+----------------------------------------------------+")
    print(f"|  RESUMEN FASE: {phase.upper():<35} |")
    print("+----------------------------------------------------+")
    print(f"|  Comandos ejecutados : {cmds:<26} |")
    print(f"|  OS detectado        : {os_type:<26} |")
    print(f"|  Comprometido        : {('SÍ' if compromised else 'no'):<26} |")
    print(f"|  Puertos abiertos    : {len(ports):<26} |")
    if ports:
        ports_str = ", ".join(str(p) for p in ports[:12])
        if len(ports) > 12:
            ports_str += ", ..."
        print(f"|     -> {ports_str}")
    print(f"|  Credenciales        : {len(creds):<26} |")
    for c in creds[:8]:
        c_short = c if len(c) <= 48 else c[:45] + "..."
        print(f"|     · {c_short}")
    if len(creds) > 8:
        print(f"|     · ... y {len(creds) - 8} más")
    print("+----------------------------------------------------+\n")


def phase_transition_node(state: PentestState):
    current = state.get("current_phase", "recon")
    new_phase = _next_phase(current)

    _print_phase_summary(current, state)
    print(f"=== [Director] {current.upper()}  →  {new_phase.upper()} ===\n")

    return {
        "current_phase": new_phase,
        "commands_in_phase": 0,
        "executed_commands": [],
        "next_tool": "",
        "next_tool_args": "FIN" if new_phase == "done" else "",
    }
