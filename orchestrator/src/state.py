from typing import TypedDict, List, Annotated
import operator

class PentestState(TypedDict):
    messages: Annotated[List[dict], operator.add]

    target_ip: str
    discovered_ports: List[int]
    current_phase: str  # "recon", "exploitation", "post-exploitation", "done"
    os_type: str        # "windows", "linux", "unknown"

    # IP del executor
    lhost: str

    is_compromised: bool
    acquired_credentials: List[str]

    last_command_output: str

    next_tool: str
    next_tool_args: str

    # Contador de fallos consecutivos
    format_retries: int

    # Comandos ejecutados
    commands_in_phase: int

    # Lista de comandos ya ejecutados
    executed_commands: List[str]
