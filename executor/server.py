from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import socket
import subprocess

app = FastAPI(title="Pentest Executor API")

#Devuelve la IP local del executor
def _lhost_for_target(target: str) -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((target, 1))   
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return ""

class CommandRequest(BaseModel):
    command: str
    timeout: int = 120 

class CommandResponse(BaseModel):
    command: str
    stdout: str
    stderr: str
    returncode: int

@app.post("/execute", response_model=CommandResponse)
def execute_command(request: CommandRequest):
    try:
        # API expuesta para el Orchestrator.
        result = subprocess.run(
            request.command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=request.timeout
        )
        return CommandResponse(
            command=request.command,
            stdout=result.stdout,
            stderr=result.stderr,
            returncode=result.returncode
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail=f"El comando excedió el tiempo límite de {request.timeout}s")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Executor is ready and waiting for commands"}

# Devuelve la IP del executor
@app.get("/lhost")
def lhost(target: str = ""):
    if not target:
        target = os.getenv("LAB_TARGET", "metasploitable")
    ip = _lhost_for_target(target)
    if not ip:
        raise HTTPException(
            status_code=503,
            detail=f"No se pudo resolver la IP local del executor hacia '{target}'."
        )
    return {"target": target, "lhost": ip}
