from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess

app = FastAPI(title="Pentest Executor API")

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
        # API solo está expuesta para el Orchestrator.
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
