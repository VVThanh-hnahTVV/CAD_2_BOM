import json
import os
import time
from collections.abc import Iterator

import httpx
from sample_data import STEPS, sample_elements

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
# Backend chưa có route; mặc định chạy mô phỏng. Đặt UI_MOCK=0 khi backend sẵn sàng.
USE_MOCK = os.getenv("UI_MOCK", "1") == "1"
MOCK_DELAY = float(os.getenv("UI_MOCK_DELAY", "0.5"))

# Route dự kiến cho từng nhánh (xem docs/PLAN.md mục 5).
BRANCH_ENDPOINTS = {"cad": "/drawings/cad", "image": "/drawings/image"}


def client() -> httpx.Client:
    return httpx.Client(base_url=API_BASE_URL, timeout=30)


def upload(branch: str, files: list[tuple[str, bytes, str]]) -> dict:
    """Gửi file tới route của nhánh. Trả {drawing_id, job_id}. files: (tên, nội dung, mime)."""
    if USE_MOCK:
        return {"drawing_id": "DRW-DEMO-001", "job_id": "JOB-DEMO-001"}
    payload = [("files", (name, data, mime)) for name, data, mime in files]
    resp = client().post(BRANCH_ENDPOINTS[branch], files=payload)
    resp.raise_for_status()
    return resp.json()


def stream_job(job_id: str, branch: str, delay: float | None = None) -> Iterator[dict]:
    """Stream tiến độ job. Mỗi sự kiện: {status, progress (0-1), step, error}."""
    if USE_MOCK:
        steps = STEPS[branch]
        for i, step in enumerate(steps, 1):
            time.sleep(MOCK_DELAY if delay is None else delay)
            done = i == len(steps)
            yield {
                "status": "succeeded" if done else "running",
                "progress": i / len(steps),
                "step": step,
                "error": None,
            }
        return
    with client().stream("GET", f"/jobs/{job_id}/events", timeout=None) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if line.startswith("data:"):
                event = json.loads(line[5:])
                yield event
                if event.get("status") in ("succeeded", "failed"):
                    return


def get_result(drawing_id: str, branch: str) -> tuple[list[dict], list[dict]]:
    """Trả (phần tử, dòng BOM kèm giá) sau khi job xong."""
    if USE_MOCK:
        from components.bom_table import build_lines

        elements = sample_elements(branch)
        return elements, build_lines(elements)
    elements = client().get(f"/drawings/{drawing_id}/elements").json()["items"]
    lines = client().get(f"/drawings/{drawing_id}/quote").json()["lines"]
    return elements, lines
