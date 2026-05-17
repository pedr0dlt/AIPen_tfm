import os
import time
import requests
from src.state import PentestState
from src.catalog import applicable_entries, format_for_prompt

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


# Borrar historial antiguo (mantener acotado el contexto)
def _prune_history(messages: list[dict]) -> list[dict]:
    if len(messages) <= _MAX_HISTORY_MESSAGES:
        return messages
    return messages[-_MAX_HISTORY_MESSAGES:]


# Nodo LLM
def llm_node(state: PentestState):
    print("\n--- [Nodo LLM] Pensando el siguiente paso... ---")

    # Cargar la plantilla del system_prompt
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "system_prompt.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        system_prompt_tpl = f.read()

    # Filtra por puertos descubiertos y SO. Si no hay puertos aún, sale vacía.
    entries = applicable_entries(
        state.get("discovered_ports", []),
        state.get("os_type", "unknown"),
    )
    exploit_table = format_for_prompt(entries)
    if entries:
        print(f"[*] Catálogo aplicable: {len(entries)} entradas → {[e['id'] for e in entries]}")

    system_prompt = system_prompt_tpl.format(
        target_ip=state["target_ip"],
        current_phase=state["current_phase"],
        discovered_ports=state["discovered_ports"],
        os_type=state.get("os_type", "unknown"),
        exploit_table=exploit_table,
    )

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
