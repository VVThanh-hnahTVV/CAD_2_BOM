import os

import httpx

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")


def client() -> httpx.Client:
    return httpx.Client(base_url=API_BASE_URL, timeout=30)
