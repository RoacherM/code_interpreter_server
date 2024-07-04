import json
import uuid
from typing import Dict, List, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from code_interpreter.async_interpreter import AsyncCodeInterpreter

app = FastAPI()

# interpreter_service = AsyncCodeInterpreter()
interpreters: Dict[str, AsyncCodeInterpreter] = {}
API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

class CodeExecutionRequest(BaseModel):
    code: str
    files: List[str] = []
    timeout: Optional[int] = 60

class CodeExecutionResponse(BaseModel):
    result: str

def get_interpreter(api_key: str = Depends(API_KEY_HEADER)) -> AsyncCodeInterpreter:
    if api_key not in interpreters:
        interpreters[api_key] = AsyncCodeInterpreter()
    return interpreters[api_key]

@app.post("/execute", response_model=CodeExecutionResponse)
async def execute_code(
    request: CodeExecutionRequest, interpreter: AsyncCodeInterpreter = Depends(get_interpreter)
):
    try:
        params = json.dumps({"code": request.code})
        result = await interpreter.call(
            params, request.files, request.timeout
        )
        return CodeExecutionResponse(result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# @app.on_event("startup")
# async def startup_event():
#     await interpreter_service.start()


@app.on_event("shutdown")
async def shutdown_event():
    for interpreter in interpreters.values():
        del interpreter
