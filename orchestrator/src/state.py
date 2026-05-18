from typing import TypedDict, List, Annotated
import operator

class PentestState(TypedDict):
    messages: Annotated[List[dict], operator.add]

    target_ip: str
    discovered_ports: List[int]
    current_phase: str  # "recon", "exploitation", "post-exploitation", "done"
    os_type: str        # "windows", "linux", "unknown"

    lhost: str

    is_compromised: bool

    # devuelve solo las creds nuevas
    acquired_credentials: Annotated[List[str], operator.add]

    last_command_output: str

    next_tool: str
    next_tool_args: str

    format_retries: int

    commands_in_phase: int

    executed_commands: List[str]
