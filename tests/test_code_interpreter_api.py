import json
from typing import List, Optional

import requests


class CodeInterpreterClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}

    def execute_code(
        self, code: str, files: List[str] = [], timeout: Optional[int] = 30
    ):
        url = f"{self.base_url}/execute"
        payload = {"code": code, "files": files, "timeout": timeout}

        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors

        return response.json()["result"]


# Example usage
if __name__ == "__main__":
    base_url = "http://0.0.0.0:8000"  # Replace with your server's URL
    api_key = "123"  # Replace with your actual API key

    client = CodeInterpreterClient(base_url, api_key)

    try:
        for i in range(5):
            result = client.execute_code(f"print('Iteration {i}')\n{i} * 2")
            print(f"Result of iteration {i}:", result)
    except requests.exceptions.RequestException as e:
        print("An error occurred:", e)
