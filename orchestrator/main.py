import os
from dotenv import load_dotenv
from src.nodes.llm_node import prewarm_ollama, llm_node

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

    print("\n[+] Enviando primer mensaje al LLM...")
    result = llm_node(initial_state)

    print("\n[LLM Response]:")
    print(result["messages"][-1]["content"])
    print("\n[+] Conexión con Ollama verificada.")


if __name__ == "__main__":
    main()
