import os
import requests
from src.state import PentestState

EXECUTOR_HOST = os.getenv("EXECUTOR_HOST", "http://localhost:8000")


def tool_node(state: PentestState):
    """
    Envía el comando al contenedor Kali (Executor) mediante su API REST,
    y devuelve la salida estándar (stdout/stderr) al agente.
    """
    comando = state.get("next_tool_args", "")
    if not comando or comando.upper() == "FIN":
        return {"last_command_output": "Ejecución finalizada por el agente."}

    print(f"--- [Nodo Tool] Ejecutando remotamente: {comando} ---")

    try:
        response = requests.post(
            f"{EXECUTOR_HOST}/execute",
            json={"command": comando, "timeout": 300},
            timeout=310
        )
        response.raise_for_status()
        result = response.json()
        output = f"[STDOUT]\n{result['stdout']}\n[STDERR]\n{result['stderr']}"
        print(f"[*] Salida recibida ({len(output)} caracteres)")
    except Exception as e:
        output = f"Error al intentar ejecutar la herramienta en Kali: {str(e)}"
        print(f"[-] {output}")

    return {
        "last_command_output": output,
        "messages": [{"role": "user", "content": f"Resultado de tu comando '{comando}':\n{output}"}],
        "next_tool": "",
        "next_tool_args": "",
        "commands_in_phase": state.get("commands_in_phase", 0) + 1,
    }
