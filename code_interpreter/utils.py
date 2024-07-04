import hashlib
import json
import os
import re
import shutil
import signal
import socket
import sys
import time
import traceback
import urllib.parse
from typing import Any, List, Literal

import json5
import requests

from code_interpreter.logger import logging


def append_signal_handler(sig, handler):
    """
    Installs a new signal handler while preserving any existing handler.
    If an existing handler is present, it will be called _after_ the new handler.
    """

    old_handler = signal.getsignal(sig)  # type: ignore
    if not callable(old_handler):
        old_handler = None  # type: ignore
        if sig == signal.SIGINT:

            def old_handler(*args, **kwargs):
                raise KeyboardInterrupt

        elif sig == signal.SIGTERM:

            def old_handler(*args, **kwargs):
                raise SystemExit

    def new_handler(*args, **kwargs):
        handler(*args, **kwargs)
        if old_handler is not None:
            old_handler(*args, **kwargs)

    signal.signal(sig, new_handler)


def get_local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def hash_sha256(text: str) -> str:
    hash_object = hashlib.sha256(text.encode())
    key = hash_object.hexdigest()
    return key


def print_traceback(is_error: bool = True):
    tb = "".join(traceback.format_exception(*sys.exc_info(), limit=3))
    if is_error:
        logging.error(tb)
    else:
        logging.warning(tb)


CHINESE_CHAR_RE = re.compile(r"[\u4e00-\u9fff]")


def has_chinese_chars(data: Any) -> bool:
    text = f"{data}"
    return bool(CHINESE_CHAR_RE.search(text))


def get_basename_from_url(path_or_url: str) -> str:
    if re.match(r"^[A-Za-z]:\\", path_or_url):
        # "C:\\a\\b\\c" -> "C:/a/b/c"
        path_or_url = path_or_url.replace("\\", "/")

    # "/mnt/a/b/c" -> "c"
    # "https://github.com/here?k=v" -> "here"
    # "https://github.com/" -> ""
    basename = urllib.parse.urlparse(path_or_url).path
    basename = os.path.basename(basename)
    basename = urllib.parse.unquote(basename)
    basename = basename.strip()

    # "https://github.com/" -> "" -> "github.com"
    if not basename:
        basename = [x.strip() for x in path_or_url.split("/") if x.strip()][-1]

    return basename


def is_http_url(path_or_url: str) -> bool:
    if path_or_url.startswith("https://") or path_or_url.startswith("http://"):
        return True
    return False


def is_image(path_or_url: str) -> bool:
    filename = get_basename_from_url(path_or_url).lower()
    for ext in ["jpg", "jpeg", "png", "webp"]:
        if filename.endswith(ext):
            return True
    return False


def sanitize_chrome_file_path(file_path: str) -> str:
    # For Linux and macOS.
    if os.path.exists(file_path):
        return file_path

    # For native Windows, drop the leading '/' in '/C:/'
    win_path = file_path
    if win_path.startswith("/"):
        win_path = win_path[1:]
    if os.path.exists(win_path):
        return win_path

    # For Windows + WSL.
    if re.match(r"^[A-Za-z]:/", win_path):
        wsl_path = f"/mnt/{win_path[0].lower()}/{win_path[3:]}"
        if os.path.exists(wsl_path):
            return wsl_path

    # For native Windows, replace / with \.
    win_path = win_path.replace("/", "\\")
    if os.path.exists(win_path):
        return win_path

    return file_path


def save_url_to_local_work_dir(url: str, save_dir: str, save_filename: str = "") -> str:
    if not save_filename:
        save_filename = get_basename_from_url(url)
    new_path = os.path.join(save_dir, save_filename)
    if os.path.exists(new_path):
        os.remove(new_path)
    logging.info(f"Downloading {url} to {new_path}...")
    start_time = time.time()
    if not is_http_url(url):
        parsed_url = urllib.parse.urlparse(url)
        path = urllib.parse.unquote(parsed_url.path)
        url = sanitize_chrome_file_path(path)
        shutil.copy(url, new_path)
    else:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            with open(new_path, "wb") as file:
                file.write(response.content)
        else:
            raise ValueError(
                "Can not download this file. Please check your network or the file link."
            )
    end_time = time.time()
    logging.info(
        f"Finished downloading {url} to {new_path}. Time spent: {end_time - start_time} seconds."
    )
    return new_path


def read_text_from_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as file:
        file_content = file.read()
    return file_content


def contains_html_tags(text: str) -> bool:
    pattern = r"<(p|span|div|li|html|script)[^>]*?"
    return bool(re.search(pattern, text))


def get_content_type_by_head_request(path: str) -> str:
    try:
        response = requests.head(path, timeout=5)
        content_type = response.headers.get("Content-Type", "")
        return content_type
    except requests.RequestException:
        return "unk"


def get_file_type(path: str) -> Literal["pdf", "docx", "pptx", "txt", "html", "unk"]:
    f_type = get_basename_from_url(path).split(".")[-1].lower()
    if f_type in ["pdf", "docx", "pptx"]:
        # Specially supported file types
        return f_type  # type: ignore

    if is_http_url(path):
        # The HTTP header information for the response is obtained by making a HEAD request to the target URL,
        # where the Content-type field usually indicates the Type of Content to be returned
        content_type = get_content_type_by_head_request(path)
        if "application/pdf" in content_type:
            return "pdf"
        elif "application/msword" in content_type:
            return "docx"

        # Assuming that the URL is HTML by default,
        # because the file downloaded by the request may contain html tags
        return "html"
    else:
        # Determine by reading local HTML file
        try:
            content = read_text_from_file(path)
        except Exception:
            print_traceback()
            return "unk"

        if contains_html_tags(content):
            return "html"
        else:
            return "txt"


def extract_urls(text: str) -> List[str]:
    pattern = re.compile(r"https?://\S+")
    urls = re.findall(pattern, text)
    return urls


def extract_code(text: str) -> str:
    # Match triple backtick blocks first
    triple_match = re.search(r"```[^\n]*\n(.+?)```", text, re.DOTALL)
    if triple_match:
        text = triple_match.group(1)
    else:
        try:
            text = json5.loads(text)["code"]  # type: ignore
        except Exception:
            print_traceback(is_error=False)
    # If no code blocks found, return original text
    # print(f"extract code:\n{text}")
    return text


# 定义改进的抽取逻辑函数
def extract_json(response):
    patterns = [
        r"```json\s*(\{.*?\})\s*```",  # 匹配 ```json {JSON} ```
        r"```\s*(\{.*?\})\s*```",  # 匹配 ``` {JSON} ```
        r"```\s*($begin:math:display$.*?$end:math:display$)\s*```",  # 匹配 ``` [JSON数组] ```
        r"```json\s*($begin:math:display$.*?$end:math:display$)\s*```",  # 匹配 ```json [JSON数组] ```
    ]
    response = response.replace("\r", "")
    for pattern in patterns:
        matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
        if matches:
            try:
                return json.loads(matches[-1].strip())
            except json.JSONDecodeError as e:
                return None
    return None
