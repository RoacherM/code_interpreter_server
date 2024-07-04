import asyncio
from typing import Dict, List, Optional, Union

from code_interpreter.interpreter import AnyThreadEventLoopPolicy, CodeInterpreter


class AsyncCodeInterpreter:
    def __init__(self, cfg: Optional[Dict] = None):
        self.interpreter = CodeInterpreter(cfg)
        asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())

    async def call(
        self,
        params: str,
        files: List[str] = [],
        timeout: Optional[int] = 30,
        **kwargs,
    ) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._execute_code_sync, params, files, timeout
        )

    def _execute_code_sync(
        self, params: str, files: List[str] = [], timeout: Optional[int] = 30
    ) -> str:
        return self.interpreter.call(params, files, timeout)

    async def start(self):
        # Any initialization code can go here
        pass

    async def stop(self):
        # Cleanup code can go here
        pass
