import asyncio
import json
import logging
from typing import List, Optional

import websockets


class CodeInterpreterClient:
    def __init__(
        self, ws_url: str, api_key: str, max_retries: int = 5, retry_delay: float = 1.0
    ):
        self.ws_url = ws_url
        self.api_key = api_key
        self.websocket = None
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logging.getLogger(__name__)

    async def connect(self):
        for attempt in range(self.max_retries):
            try:
                self.websocket = await websockets.connect(
                    self.ws_url, extra_headers={"X-API-Key": self.api_key}
                )
                self.logger.info("Connected to WebSocket server")
                return
            except Exception as e:
                self.logger.error(f"Connection attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
        raise ConnectionError("Failed to connect after maximum retries")

    async def execute_code(
        self, code: str, files: List[str] = [], timeout: Optional[int] = 30
    ):
        if not self.websocket:
            await self.connect()

        request = {"type": "execute", "code": code, "files": files, "timeout": timeout}

        try:
            await self.websocket.send(json.dumps(request))
            response = await self.websocket.recv()
            return json.loads(response)["result"]
        except websockets.exceptions.ConnectionClosed:
            self.logger.warning(
                "WebSocket connection closed. Attempting to reconnect..."
            )
            await self.connect()
            return await self.execute_code(code, files, timeout)  # Retry the request

    # async def close(self):
    #     if self.websocket:
    #         await self.websocket.close()
    #         self.logger.info("WebSocket connection closed")

    async def close(self):
        if self.websocket:
            try:
                if self.websocket.open:
                    release_request = {"type": "release"}
                    await self.websocket.send(json.dumps(release_request))
                    try:
                        response = await asyncio.wait_for(
                            self.websocket.recv(), timeout=10
                        )
                        response_data = json.loads(response)
                        if "success" in response_data.get("result"):
                            self.logger.info("Interpreter released successfully")
                        else:
                            self.logger.error("Failed to release interpreter")
                    except Exception as e:
                        self.logger.warning(f"Failed to release interpreter: {str(e)}")
            except Exception as e:
                self.logger.warning(f"Failed to close WebSocket connection: {str(e)}")
            finally:
                await self.websocket.close()
                self.websocket = None
                self.logger.info("WebSocket connection closed")


async def main():
    logging.basicConfig(level=logging.INFO)
    client = CodeInterpreterClient("ws://localhost:8000/ws", "your-api-key")

    try:
        
        result = await client.execute_code("print('Hello, World!')")
        print(f"Result: {result}")

        # result2 = await client.execute_code("print('Another execution')\nimport time\ntime.sleep(35)", timeout=90)
        # print(f"Result 2: {result2}")
        
        for i in range(5):
            result = await client.execute_code(f"print('Iteration {i}')\n{i} * 2")
            print(f"Result of iteration {i}:", result)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
