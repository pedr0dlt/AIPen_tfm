import os
import requests
from dotenv import load_dotenv

from src.agent import build_graph
from src.nodes.llm_node import prewarm_ollama
from src.catalog import load_catalog

load_dotenv()

EXECUTOR_HOST = os.getenv("EXECUTOR_HOST", "http://localhost:8000")


def _get_lhost(target: str) -> str:
    try:
        r = requests.get(
            f"{EXECUTOR_HOST}/lhost",
            params={"target": target},
            timeout=5,
        )
        r.raise_for_status()
        lhost = r.json().get("lhost", "")
        if lhost:
            print(f"[*] LHOST del executor en red `lab`: {lhost}")
            return lhost
    except Exception as e:
        print(f"[!] No se pudo obtener LHOST del executor: {e}")
    return ""


def main():
    target_ip = os.getenv("TARGET_IP", "127.0.0.1")
    print("========================================")
    print(f" AIPen — Objetivo: {target_ip}")
    print("========================================")

    # Pre-carga porque sino se tira 5 minutos sin arrancar
    prewarm_ollama()

    catalog = load_catalog()
    if not catalog:
        print("[!] AVISO: catálogo vacío o no encontrado. El agente sólo podrá")
        print("    ejecutar comandos shell (sin exploits del catálogo).")

    lhost = _get_lhost(target_ip)

    initial_state = {
        "messages": [
            {
                "role": "user",
                "content": (
                    f"Comienza la auditoría del objetivo {target_ip}. "
                    f"Tu primer paso DEBE ser un escaneo nmap para descubrir "
                    f"puertos y servicios. Responde únicamente con un objeto "
                    f"JSON válido siguiendo el formato indicado en el system "
                    f"prompt."
                ),
            }
        ],
        "target_ip": target_ip,
        "discovered_ports": [],
        "current_phase": "recon",
        "os_type": "unknown",
        "lhost": lhost,
        "is_compromised": False,
        "acquired_credentials": [],
        "last_command_output": "",
        "next_tool": "",
        "next_tool_args": "",
        "format_retries": 0,
        "commands_in_phase": 0,
        "executed_commands": [],
    }

    agent = build_graph()

    print("\n[+] Arrancando ciclo ReAct LangGraph (F1: YAML + JSON)...")
    final_state = dict(initial_state)
    try:
        for chunk in agent.stream(initial_state, {"recursion_limit": 150}, stream_mode="values"):
            final_state = chunk
    except Exception as e:
        print(f"\n[!] Ejecución interrumpida: {e}")

    print("\n[+] Ciclo completado.")
    print("============================================================")
    print(f"  Objetivo            : {final_state.get('target_ip')}")
    print(f"  Fase final          : {final_state.get('current_phase')}")
    print(f"  OS detectado        : {final_state.get('os_type')}")
    ports = final_state.get('discovered_ports', []) or []
    print(f"  Puertos abiertos    : {len(ports)} → {ports}")
    print(f"  Comandos ejecutados : {final_state.get('commands_in_phase', 0)}")
    print("============================================================")


if __name__ == "__main__":
    main()
