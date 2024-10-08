import asyncio
import json
from concurrent.futures import ThreadPoolExecutor, TimeoutError
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

executor = ThreadPoolExecutor(max_workers=50) # 设置最大线程数为 50


def get_interpreter(api_key: str) -> CodeInterpreter:
    if api_key not in interpreters:
        interpreters[api_key] = CodeInterpreter()
    return interpreters[api_key]


def remove_interpreter(api_key: str):
    if api_key in interpreters:
        interpreter = interpreters.pop(api_key)
        interpreter.__del__() # 手动调用 interpreter 的 __del__ 方法
        logging.info(f"Removed interpreter for API key: {api_key}")


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
                logging.info(f"Received request: {data}")

                try:
                    # 在线程池中运行同步的 interpreter.call 方法
                    future = executor.submit(
                        interpreter.call, params=json.dumps({"code": code}), files=files, timeout=timeout
                    )

                    # 等待结果，设置超时
                    result = await asyncio.get_event_loop().run_in_executor(
                        None, future.result, timeout
                    )
                    await websocket.send_json({"result": result, "status": "success"})
                except TimeoutError:
                    logging.warning(f"Execution timed out after {timeout} seconds")
                    remove_interpreter(api_key)
                    await websocket.send_json({"result": f"Execution timed out after {timeout} seconds", "status": "error"})
                    await websocket.close(code=4000, reason="Execution timed out")
                except Exception as e:
                    remove_interpreter(api_key)
                    await websocket.send_json({"result": str(e), "status": "error"})
            elif data["type"] == "release":
                remove_interpreter(api_key)
                await websocket.send_json({"result": "Interpreter released", "status": "success"})
            else:
                await websocket.send_json({"result": "Unknown request type", "status": "error"})
    except WebSocketDisconnect:
        logging.info("WebSocket disconnected")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
