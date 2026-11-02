from pathlib import Path

import api_client
from components.bom_table import build_lines
from components.drawing_view import draw_boxes
from PIL import Image
from sample_data import sample_elements, scale_bbox
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_stream_mock_ends_succeeded():
    events = list(api_client.stream_job("J", "image", delay=0))
    assert events[-1]["status"] == "succeeded" and events[-1]["progress"] == 1.0
    assert all(e["status"] == "running" for e in events[:-1])
    assert [e["progress"] for e in events] == sorted(e["progress"] for e in events)


def test_bom_groups_and_keeps_source_ids():
    lines = build_lines(sample_elements("cad"))
    assert sum(len(ln["source_ids"]) for ln in lines) == 5
    wall = next(ln for ln in lines if ln["class"] == "wall")
    assert wall["unit"] == "m" and wall["qty"] == 12.4
    eq = next(ln for ln in lines if ln["class"] == "equipment")
    assert eq["unit_price"] is None and eq["amount"] is None


def test_image_branch_has_no_handle_and_lower_confidence():
    cad, img = sample_elements("cad"), sample_elements("image")
    assert all(e["handle"] is None for e in img)
    assert all(i["confidence"] < c["confidence"] for i, c in zip(img, cad, strict=True))


def test_scale_bbox_fits_image():
    for e in sample_elements("image"):
        x0, y0, x1, y1 = scale_bbox(e["bbox"], (1040, 720))
        assert 0 <= x0 < x1 <= 1040 and 0 <= y0 < y1 <= 720


def test_draw_boxes_highlights_only_selected():
    img = Image.new("RGB", (520, 360), (255, 255, 255))
    els = sample_elements("image")
    assert draw_boxes(img, els, set()).tobytes() == img.tobytes()
    out = draw_boxes(img, els, {"D-01"})
    assert out.size == img.size and out.tobytes() != img.tobytes()


def test_app_renders_empty():
    at = AppTest.from_file(str(APP), default_timeout=20).run()
    assert not at.exception
    assert at.button[0].disabled  # chưa có file thì chưa bấm được


def test_app_renders_with_result():
    at = AppTest.from_file(str(APP), default_timeout=20)
    els = sample_elements("cad")
    at.session_state["result"] = {"elements": els, "lines": build_lines(els), "branch": "cad"}
    at.session_state["sig"] = ()
    at.run()
    assert not at.exception
    assert any("Dòng chưa có giá" in w.value for w in at.warning)
