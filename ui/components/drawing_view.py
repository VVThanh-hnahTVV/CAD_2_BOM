from PIL import Image, ImageDraw


def draw_boxes(image: Image.Image, elements: list[dict], highlight_ids: set[str]) -> Image.Image:
    """Vẽ bbox lên ảnh. Phần tử trong highlight_ids được tô sáng; không chọn gì thì chỉ vẽ ảnh gốc."""
    img = image.convert("RGB").copy()
    if not highlight_ids:
        return img
    d = ImageDraw.Draw(img, "RGBA")
    width = max(3, img.width // 200)
    for e in elements:
        if e["id"] not in highlight_ids:
            continue
        x0, y0, x1, y1 = e["bbox"]
        d.rectangle(
            [x0, y0, x1, y1], outline=(230, 50, 20, 255), fill=(230, 50, 20, 50), width=width
        )
        d.text((x0 + 2, max(y0 - 12, 0)), e["id"], fill=(230, 50, 20, 255))
    return img
