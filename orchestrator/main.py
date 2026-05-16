import os
from dotenv import load_dotenv
from src.agent import build_graph
from src.nodes.llm_node import prewarm_ollama

load_dotenv()


def main():
    target_ip = os.getenv("TARGET_IP", "127.0.0.1")
    print("========================================")
    print(f" Objetivo: {target_ip}")
    print("========================================")

    # Pre-carga porque sino se tira 5 minutos sin arrancar
    prewarm_ollama()

    initial_state = {
        "messages": [
            {
                "role": "user",
                "content": (
                    f"Inicia la fase de reconocimiento sobre el objetivo {target_ip}. "
                    f"Ejecuta el primer comando nmap."
                ),
            }
        ],
        "target_ip": target_ip,
        "discovered_ports": [],
        "current_phase": "recon",
        "os_type": "unknown",
        "lhost": "",
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

    print("\n[+] Arrancando ciclo ReAct LangGraph...")
    final_state = dict(initial_state)
    try:
        for chunk in agent.stream(initial_state, {"recursion_limit": 150}, stream_mode="values"):
            final_state = chunk
    except Exception as e:
        print(f"\n[!] Ejecución interrumpida: {e}")

    print("\n[+] Ciclo ReAct completado.")
    print(f"    Puertos descubiertos: {final_state.get('discovered_ports', [])}")
    print(f"    Comandos ejecutados : {final_state.get('commands_in_phase', 0)}")


if __name__ == "__main__":
    main()
