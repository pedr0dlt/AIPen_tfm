from langgraph.graph import StateGraph, END
from src.state import PentestState
from src.nodes.llm_node import llm_node
from src.nodes.parser_node import parser_node
from src.nodes.tool_node import tool_node

MAX_FORMAT_RETRIES = 3


def route_next_step(state: PentestState):
    """Arista condicional tras el parser."""
    args = state.get("next_tool_args", "")
    next_tool = state.get("next_tool")

    if args.upper() == "FIN":
        return END

    if next_tool == "executor":
        return "tool"

    if next_tool == "retry":
        return "llm"

    retries = state.get("format_retries", 0)
    if retries >= MAX_FORMAT_RETRIES:
        print(f"[!] Límite de {MAX_FORMAT_RETRIES} reintentos de formato alcanzado. Abortando.")
        return END

    return "enforce_format"


def check_parser_fails(state: PentestState):
    """Nodo de contingencia para JSON inválido."""
    retries = state.get("format_retries", 0) + 1
    print(f"--- [Nodo Contingencia] Forzando formato JSON (intento {retries}/{MAX_FORMAT_RETRIES}) ---")
    return {
        "format_retries": retries,
        "messages": [{
            "role": "user",
            "content": (
                "[SISTEMA] No has devuelto un objeto JSON válido. "
                "Responde EXCLUSIVAMENTE con un objeto JSON. "
                'Ejemplos válidos:\n'
                '  {"action": "shell", "command": "nmap -Pn -sV ..."}\n'
                '  {"action": "exploit", "exploit_id": "vsftpd_234_backdoor"}\n'
                '  {"action": "FIN"}\n'
                "Sin texto antes ni después, sin bloques markdown."
            )
        }]
    }


def reset_retries(state: PentestState):
    return {"format_retries": 0}


def build_graph():
    workflow = StateGraph(PentestState)

    workflow.add_node("llm", llm_node)
    workflow.add_node("parser", parser_node)
    workflow.add_node("enforce_format", check_parser_fails)
    workflow.add_node("tool", tool_node)
    workflow.add_node("reset_retries", reset_retries)

    workflow.set_entry_point("llm")

    workflow.add_edge("llm", "parser")

    workflow.add_conditional_edges(
        "parser",
        route_next_step,
        {
            "tool": "reset_retries",
            "llm": "llm",                   # F1 — ruta "retry"
            "enforce_format": "enforce_format",
            END: END,
        }
    )

    workflow.add_edge("reset_retries", "tool")
    workflow.add_edge("tool", "llm")
    workflow.add_edge("enforce_format", "llm")

    return workflow.compile()
