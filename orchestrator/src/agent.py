from langgraph.graph import StateGraph, END
from src.state import PentestState
from src.nodes.llm_node import llm_node
from src.nodes.parser_node import parser_node
from src.nodes.tool_node import tool_node

MAX_FORMAT_RETRIES = 3

# Arista condicional
def route_next_step(state: PentestState):
    next_tool = state.get("next_tool")
    args = state.get("next_tool_args", "")

    if args.upper() == "FIN":
        return END

    if next_tool == "executor":
        return "tool"

    retries = state.get("format_retries", 0)
    if retries >= MAX_FORMAT_RETRIES:
        print(f"[!] Límite de {MAX_FORMAT_RETRIES} reintentos alcanzado. Abortando.")
        return END

    return "enforce_format"

# Checkea formato incorrecto
def check_parser_fails(state: PentestState):
    retries = state.get("format_retries", 0) + 1
    print(f"--- [Nodo Contingencia] Forzando formato correcto (intento {retries}/{MAX_FORMAT_RETRIES}) ---")
    return {
        "format_retries": retries,
        "messages": [{
            "role": "user",
            "content": (
                "SISTEMA: No has utilizado el formato de salida requerido. "
                "Para ejecutar un comando DEBES usar exactamente: "
                "<comando>EL_COMANDO</comando>. "
                "Si no tienes nada más que hacer, responde <comando>FIN</comando>."
            )
        }]
    }


def reset_retries(state: PentestState):
    return {"format_retries": 0}

# Crea el grafo ReAct
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
            "enforce_format": "enforce_format",
            END: END
        }
    )

    workflow.add_edge("reset_retries", "tool")
    workflow.add_edge("tool", "llm")
    workflow.add_edge("enforce_format", "llm")

    return workflow.compile()
