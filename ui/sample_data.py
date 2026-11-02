"""Dữ liệu MINH HỌA cho demo. Không phải kết quả nhận diện hay đo thật."""

# Khung chuẩn mà bbox mẫu được vẽ trên đó; UI co giãn bbox sang kích thước ảnh người dùng tải lên.
SAMPLE_CANVAS = (520, 360)

# (id, class, spec, số lượng hoặc chiều dài m, là chiều dài?, handle, bbox, confidence)
_BASE = [
    ("D-01", "door", "W800", 1, False, "2F3A", [412, 208, 452, 248], 0.97),
    ("D-02", "door", "W900", 1, False, "2F3B", [300, 208, 340, 248], 0.95),
    ("WD-03", "window", "W1200", 2, False, "2F40", [120, 40, 200, 60], 0.62),
    ("W-12", "wall", "BTCT t=180", 12.4, True, "2F51", [40, 300, 480, 312], 0.91),
    (
        "EQ-07",
        "equipment",
        "Điều hòa âm trần 4 hướng",
        1,
        False,
        "2F77",
        [250, 120, 290, 160],
        0.55,
    ),
]

# Đơn giá minh họa (đồng). EQ-07 cố ý không có giá để thấy cờ "chưa có giá".
PRICES = {
    ("door", "W800"): 3_200_000,
    ("door", "W900"): 3_500_000,
    ("window", "W1200"): 2_800_000,
    ("wall", "BTCT t=180"): 1_900_000,
}

LOW_CONFIDENCE = 0.7  # ngưỡng minh họa để gắn cờ

# Các bước mô phỏng, theo từng nhánh (khớp sơ đồ pipeline trong docs/PLAN.md)
STEPS = {
    "cad": ["Lưu bản gốc", "Đọc file", "Kiểm kê", "Dựng đối tượng", "Phân loại", "Đếm, đo"],
    "image": [
        "Lưu bản gốc",
        "Tiền xử lý",
        "Detect, segment",
        "OCR",
        "Hiệu chỉnh tỷ lệ",
        "Đếm, đo",
    ],
}


def sample_elements(branch: str) -> list[dict]:
    """Phần tử theo dạng JSON chuẩn. Nhánh ảnh: không có handle, confidence thấp hơn."""
    out = []
    for eid, cls, spec, value, is_len, handle, bbox, conf in _BASE:
        is_image = branch == "image"
        el = {
            "id": eid,
            "class": cls,
            "spec": spec,
            "source": branch,
            "view": "plan_1F",
            "handle": None if is_image else handle,
            "bbox": bbox,
            "confidence": round(conf * 0.9, 2) if is_image else conf,
        }
        el["length_m" if is_len else "qty"] = value
        out.append(el)
    return out


def scale_bbox(bbox: list[float], size: tuple[int, int]) -> list[int]:
    """Co giãn bbox từ khung mẫu sang kích thước ảnh (w, h)."""
    sx, sy = size[0] / SAMPLE_CANVAS[0], size[1] / SAMPLE_CANVAS[1]
    x0, y0, x1, y1 = bbox
    return [round(x0 * sx), round(y0 * sy), round(x1 * sx), round(y1 * sy)]
