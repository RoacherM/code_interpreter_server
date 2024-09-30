<!--
 * @Author: ByronVon
 * @Date: 2024-07-03 20:23:11
 * @FilePath: /code_interpreter_server/README.md
 * @Description: 
-->
# 说明

这个repo提供了一个Jupyter运行环境，用于执行python相关的代码。

# Build the Docker image
```
docker build -t code_interpreter:latest .
```

# Run the Docker container
```
docker run -d -v /tmp/workspace:/tmp/workspace -p 8000:8000 --name ci code_interpreter:latest 
```

# Test
```python
python tests/test_code_interpreter_ws.py
```
