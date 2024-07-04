'''
Author: ByronVon
Date: 2024-07-03 17:09:20
FilePath: /code_interpreter_server/client.py
Description: 
'''
import asyncio

import aiohttp

API_KEY = "xxx"

async def execute_code(session, code):
    async with session.post(
        "http://0.0.0.0:8000/execute",
        json={"code": code, "timeout": 10},
        headers={"X-API-Key": API_KEY},
    ) as response:
        return await response.json()


async def test_execute_code():
    async with aiohttp.ClientSession() as session:
        # 第一次执行
        result1 = await execute_code(session, "x = 5")
        print("Result 1:", result1)

        # 第二次执行，使用前一次定义的变量
        result2 = await execute_code(session, "print(x)")
        print("Result 2:", result2)

        # 第三次执行，进行计算
        result3 = await execute_code(session, "y = x * 2\nprint(y)")
        print("Result 3:", result3)

        # 第四次执行，进行计算
        result4 = await execute_code(session, "y = y ** 2\ny")
        print("Result 4:", result4)
        
if __name__ == "__main__":
    asyncio.run(test_execute_code())
