import json
from typing import Dict
from uuid import uuid4

import uvicorn
from fastapi import Depends, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.security import APIKeyHeader

from code_interpreter.interpreter import CodeInterpreter
from code_interpreter.logger import logging

app = FastAPI()

interpreters: Dict[str, CodeInterpreter] = {}
API_KEY_HEADER = APIKeyHeader(name="X-API-Key")


def get_interpreter(api_key: str) -> CodeInterpreter:
    if api_key not in interpreters:
        interpreters[api_key] = CodeInterpreter()
    return interpreters[api_key]


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    api_key = websocket.headers.get("X-API-Key")

    if not api_key:
        await websocket.close(code=4000, reason="API Key is required")
        return

    interpreter = get_interpreter(api_key)

    try:
        while True:
            data = await websocket.receive_json()
            if data["type"] == "execute":
                code = data["code"]
                files = data.get("files", [])
                timeout = data.get("timeout", 30)

                logging.info(f"Executing code: {code}")

                try:
                    result = interpreter.call(
                        params=json.dumps({"code": code}),
                        files=files,
                        timeout=timeout,
                    )
                    await websocket.send_json({"result": result})
                except Exception as e:
                    await websocket.send_json({"error": str(e)})
            else:
                await websocket.send_json({"error": "Unknown request type"})
    except WebSocketDisconnect:
        logging.info("WebSocket disconnected")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
