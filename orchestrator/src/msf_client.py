from __future__ import annotations

import os
import re
import time
import threading
from typing import Optional


_lock = threading.Lock()
_client = None          
_console = None          
_disabled = False        


def _get_client():
    global _client, _disabled
    if _disabled:
        return None
    if _client is not None:
        return _client
    with _lock:
        if _client is not None:
            return _client
        try:
            from pymetasploit3.msfrpc import MsfRpcClient
            host = os.getenv("MSF_RPC_HOST", "executor")
            port = int(os.getenv("MSF_RPC_PORT", "55553"))
            user = os.getenv("MSF_RPC_USER", "msf")
            password = os.getenv("MSF_RPC_PASS", "msf123")
            _client = MsfRpcClient(
                password,
                server=host,
                port=port,
                username=user,
                ssl=False,
            )
            print(f"[msf_client] Conectado a msfrpcd en {host}:{port}")
            return _client
        except Exception as e:
            print(f"[msf_client] No disponible — fallback a subprocess. Causa: {e}")
            _disabled = True
            return None


def _get_console():
    global _console
    if _disabled:
        return None
    if _console is not None:
        return _console
    with _lock:
        if _console is not None:
            return _console
        client = _get_client()
        if client is None:
            return None
        try:
            _console = client.consoles.console()
            time.sleep(2)
            try:
                _console.read()
            except Exception:
                pass
            print(f"[msf_client] Console persistente abierta (cid={_console.cid})")
            return _console
        except Exception as e:
            print(f"[msf_client] No se pudo abrir console RPC: {e}")
            return None


_MSF_X_DOUBLE = re.compile(r'msfconsole\s+-q\s+-x\s+"(.+)"\s*$', re.DOTALL)
_MSF_X_SINGLE = re.compile(r"msfconsole\s+-q\s+-x\s+'(.+)'\s*$", re.DOTALL)


def _extract_x_payload(command: str) -> Optional[str]:
    cmd = command.strip()
    for regex in (_MSF_X_DOUBLE, _MSF_X_SINGLE):
        m = regex.search(cmd)
        if m:
            return m.group(1)
    return None


def _normalize_session_ids(chain: str, client) -> str:
    try:
        sessions = client.sessions.list or {}
        if not sessions:
            return chain
        latest = max(int(sid) for sid in sessions.keys())
        return re.sub(r"sessions\s+-i\s+\d+", f"sessions -i {latest}", chain)
    except Exception:
        return chain


def _wait_until_idle(console, max_seconds: int) -> str:
    output = ""
    idle_streak = 0
    elapsed = 0
    POLL = 1
    while elapsed < max_seconds:
        time.sleep(POLL)
        elapsed += POLL
        try:
            chunk = console.read()
        except Exception as e:
            output += f"\n[msf_client] read falló: {e}"
            break
        data = chunk.get("data", "") or ""
        output += data
        if chunk.get("busy", True):
            idle_streak = 0
        else:
            if data.strip():
                idle_streak = 0  
            else:
                idle_streak += POLL
                if idle_streak >= 3:
                    return output
    return output + f"\n[msf_client] timeout {max_seconds}s sin completar"


def is_available() -> bool:
    return _get_client() is not None


def list_sessions() -> dict:
    client = _get_client()
    if client is None:
        return {}
    try:
        raw = client.sessions.list or {}
        return {str(k): v for k, v in raw.items()}
    except Exception as e:
        print(f"[msf_client] list_sessions falló: {e}")
        return {}


def latest_session_info() -> Optional[dict]:
    sessions = list_sessions()
    if not sessions:
        return None
    try:
        latest_id = max(int(k) for k in sessions.keys())
    except ValueError:
        return None
    info = sessions.get(str(latest_id), {}) or {}
    return {
        "id": latest_id,
        "type": str(info.get("type", "unknown")),
        "via_exploit": str(info.get("via_exploit", "unknown")),
    }


def execute_via_console(command: str, total_timeout: int = 240) -> Optional[str]:
    payload = _extract_x_payload(command)
    if payload is None:
        return None  

    client = _get_client()
    console = _get_console()
    if client is None or console is None:
        return None 

    statements = [s.strip() for s in payload.split(";")]
    statements = [s for s in statements
                  if s and not re.match(r"^exit(\s+-y)?$", s, re.I)]

    statements = [_normalize_session_ids(s, client) for s in statements]

    try:
        console.read()
    except Exception:
        pass

    output_acc = ""
    deadline = time.monotonic() + total_timeout

    for stmt in statements:
        if time.monotonic() > deadline:
            output_acc += "\n[msf_client] timeout global, abortando cadena"
            break

        try:
            console.write(stmt + "\n")
        except Exception as e:
            output_acc += f"\n[msf_client] write falló: {e}"
            break

        output_acc += f"\n>> {stmt}\n"

        per_cmd = 90
        sleep_match = re.match(r"sleep\s+(\d+)", stmt, re.I)
        if sleep_match:
            per_cmd = int(sleep_match.group(1)) + 10
        per_cmd = min(per_cmd, max(1, int(deadline - time.monotonic())))
        output_acc += _wait_until_idle(console, max_seconds=per_cmd)

    return output_acc
