from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import os
import asyncio

app = FastAPI()

SCRIPTS_DIRECTORY = os.getenv("SCRIPTS_DIRECTORY")

class ScriptRequest(BaseModel):
    script_name: str

class ScriptResult(BaseModel):
    output: str
    error: str
    return_code: int

@app.post("/run_script", response_model=ScriptResult)
async def run_script(request: ScriptRequest):
    script_name = request.script_name
    script_path = os.path.join(SCRIPTS_DIRECTORY, script_name)

    if not os.path.exists(script_path):
        raise HTTPException(status_code=404, detail=f"Script {script_name} not found")

    try:
        process = await asyncio.create_subprocess_exec(
            'bash', script_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        output = stdout.decode('utf-8', errors='ignore')
        error = stderr.decode('utf-8', errors='ignore')
        return_code = process.returncode

        return ScriptResult(output=output, error=error, return_code=return_code)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/list_scripts")
async def list_scripts():
    try:
        scripts = [f for f in os.listdir(SCRIPTS_DIRECTORY) if os.path.isfile(os.path.join(SCRIPTS_DIRECTORY, f)) and f.endswith('.sh')]
        return {"scripts": scripts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
