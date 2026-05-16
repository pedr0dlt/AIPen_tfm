import re
from src.state import PentestState

# Analiza la respuesta buscando la etiqueta <comando>...</comando>
def parser_node(state: PentestState):
    print("--- [Nodo Parser] Extrayendo comando... ---")
    last_message = state["messages"][-1]["content"]

    # Buscar el patrón <comando>...</comando> usando expresiones regulares
    match = re.search(r"<comando>(.*?)</comando>", last_message, re.IGNORECASE | re.DOTALL)

    if match:
        comando = match.group(1).strip()
        print(f"[*] Comando detectado: {comando}")
        return {
            "next_tool": "executor",
            "next_tool_args": comando
        }
    else:
        print("[-] No se detectó ninguna etiqueta de comando en la respuesta.")
        return {
            "next_tool": "none",
            "next_tool_args": ""
        }
