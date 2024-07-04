'''
Author: ByronVon
Date: 2024-07-03 16:57:21
FilePath: /code_interpreter_server/tests/test_code_interpreter.py
Description: 
'''
import json

from code_interpreter.async_interpreter import AsyncCodeInterpreter
from code_interpreter.interpreter import CodeInterpreter


def test_code_interpreter():
    code_interpreter = CodeInterpreter()
    # Define the multiline code to be executed
    multiline_code = """
import pandas as pd
# Create a DataFrame
data = {
    'A': [1,2],
    'B': [3,4],
    'C': [5,6]
}
df = pd.DataFrame(data)

# Perform a simple operation
df['D'] = df['A'] + df['B']

# Print the DataFrame
print(df)
    """
    result = code_interpreter.call(
        params=json.dumps({"code": multiline_code}), timeout=10
    )

    # Print the result
    print("*" * 20)
    print(f"result: {result}")
    print("*" * 20)


async def test_code_interpreter_async():

    code_interpreter = AsyncCodeInterpreter()
    code = """
## 测试
x = 5+3
print(x)
x
"""
    await code_interpreter.start()
    result = await code_interpreter.call(json.dumps({"code": code}), timeout=10)
    print(result)
    print("*" * 20)
    print(f"result: {result}")
    print("*" * 20)


if __name__ == "__main__":
    import asyncio

    test_code_interpreter()
    asyncio.run(test_code_interpreter_async())
