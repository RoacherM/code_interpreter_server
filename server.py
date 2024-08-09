import json
from typing import Dict, List, Optional
from uuid import uuid4

import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from code_interpreter.interpreter import CodeInterpreter
from code_interpreter.logger import logging

app = FastAPI()

# 用于存储 API key 到 CodeInterpreter 实例的映射
interpreters: Dict[str, CodeInterpreter] = {}
API_KEY_HEADER = APIKeyHeader(name="X-API-Key")


class CodeRequest(BaseModel):
    code: str
    files: List[str] = []
    timeout: Optional[int] = 30


def get_interpreter(api_key: str = Depends(API_KEY_HEADER)) -> CodeInterpreter:
    if api_key not in interpreters:
        interpreters[api_key] = CodeInterpreter()
    return interpreters[api_key]

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/execute")
def execute_code(request: CodeRequest, interpreter: CodeInterpreter = Depends(get_interpreter)):
    logging.info(f"Request data: {request}")


    try:
        result = interpreter.call(
            params=json.dumps({"code": request.code}),
            files=request.files,
            timeout=request.timeout,
        )
        return JSONResponse(content={"result": result})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
