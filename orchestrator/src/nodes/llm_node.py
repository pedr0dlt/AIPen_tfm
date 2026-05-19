import os
import time
import requests
from src.state import PentestState
from src.catalog import applicable_entries, format_for_prompt
from src.nodes.knowledge_node import load_playbook

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen2.5:3b")

# Parámetros
_LLM_TIMEOUT = 600           
_MAX_OUTPUT_TOKENS = 220     
_KEEP_ALIVE = "30m"
_MAX_HISTORY_MESSAGES = 5    


# Calentamiento
def prewarm_ollama() -> None:
    print(f"[*] Pre-cargando modelo '{MODEL_NAME}' en Ollama")
    t0 = time.monotonic()
    try:
        requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json={
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": "ping"}],
                "stream": False,
                "keep_alive": _KEEP_ALIVE,
                "options": {"num_predict": 1, "temperature": 0.0},
            },
            timeout=_LLM_TIMEOUT,
        )
        elapsed = time.monotonic() - t0
        print(f"[*] Modelo listo en {elapsed:.1f}s")
    except Exception as e:
        elapsed = time.monotonic() - t0
        print(f"[!] Pre-warm fallido tras {elapsed:.1f}s: {e}")


# Borrar historial antiguo
def _prune_history(messages: list[dict]) -> list[dict]:
    if len(messages) <= _MAX_HISTORY_MESSAGES:
        return messages
    return messages[-_MAX_HISTORY_MESSAGES:]


_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "prompts")
_PHASE_PROMPT_FILES = {
    "recon":              "system_prompt_recon.txt",
    "exploitation":       "system_prompt_exploitation.txt",
    "post-exploitation":  "system_prompt_postexploit.txt",
}

# Lee el prompt de la fase
def _load_phase_prompt(phase: str) -> str:
    filename = _PHASE_PROMPT_FILES.get(phase, "system_prompt_recon.txt")
    path = os.path.join(_PROMPTS_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# Nodo LLM
def llm_node(state: PentestState):
    phase = state.get("current_phase", "recon")
    print(f"\n--- [Nodo LLM | fase={phase}] Pensando el siguiente paso... ---")

    system_prompt_tpl = _load_phase_prompt(phase)

    entries = applicable_entries(
        state.get("discovered_ports", []),
        state.get("os_type", "unknown"),
    )
    exploit_table = format_for_prompt(entries)
    if entries and phase == "exploitation":
        print(f"[*] Catálogo aplicable: {len(entries)} entradas → {[e['id'] for e in entries]}")
    playbook_context = load_playbook(
        phase=phase,
        os_type=state.get("os_type", "unknown"),
        open_ports=state.get("discovered_ports", []),
        last_output=state.get("last_command_output", ""),
    )

    # Variables usadas
    fmt_vars = {
        "target_ip": state["target_ip"],
        "current_phase": phase,
        "discovered_ports": state["discovered_ports"],
        "os_type": state.get("os_type", "unknown"),
        "exploit_table": exploit_table,
        "is_compromised": state.get("is_compromised", False),
        "n_credentials": len(state.get("acquired_credentials", []) or []),
        "executed_commands": state.get("executed_commands", []) or [],
        "last_session_id": state.get("last_session_id", 0) or 0,
        "playbook_context": playbook_context,
    }
    system_prompt = system_prompt_tpl.format(**fmt_vars)

    pruned = _prune_history(state["messages"])
    print(f"[*] Historial: {len(state['messages'])} mensajes totales → "
          f"{len(pruned)} enviados al LLM")

    payload_messages = [{"role": "system", "content": system_prompt}]
    payload_messages.extend(pruned)

    payload = {
        "model": MODEL_NAME,
        "messages": payload_messages,
        "stream": False,
        "keep_alive": _KEEP_ALIVE,
        "format": "json",   
        "options": {
            "temperature": 0.1,          
            "num_predict": _MAX_OUTPUT_TOKENS,
        }
    }

    t0 = time.monotonic()
    try:
        response = requests.post(f"{OLLAMA_HOST}/api/chat", json=payload, timeout=_LLM_TIMEOUT)
        response.raise_for_status()
        llm_response = response.json()["message"]["content"]
        elapsed = time.monotonic() - t0
        print(f"[*] Respuesta del LLM ({len(llm_response)} chars) en {elapsed:.1f}s")
        return {
            "messages": [{"role": "assistant", "content": llm_response}]
        }
    except Exception as e:
        elapsed = time.monotonic() - t0
        print(f"[-] Error en Ollama tras {elapsed:.1f}s: {e}")
        return {
            "messages": [{
                "role": "user",
                "content": (
                    "[SISTEMA] Tu respuesta anterior no llegó (timeout o error de red). "
                    "Reintenta tu acción siguiendo las reglas del system prompt. "
                    "Si ya hay puertos descubiertos, usa action='exploit' con un "
                    "exploit_id de la lista — NO repitas nmap."
                )
            }]
        }
