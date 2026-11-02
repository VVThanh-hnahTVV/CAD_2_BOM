from sample_data import PRICES


def build_lines(elements: list[dict]) -> list[dict]:
    """Nhóm theo class + spec, cộng số lượng/chiều dài, giữ ID nguồn. Dùng cho chế độ mô phỏng."""
    groups: dict[tuple[str, str], dict] = {}
    for e in elements:
        is_len = "length_m" in e
        g = groups.setdefault(
            (e["class"], e["spec"]),
            {
                "class": e["class"],
                "spec": e["spec"],
                "qty": 0,
                "unit": "m" if is_len else "bộ",
                "source_ids": [],
            },
        )
        g["qty"] += e["length_m"] if is_len else e["qty"]
        g["source_ids"].append(e["id"])
    lines = []
    for g in groups.values():
        price = PRICES.get((g["class"], g["spec"]))
        g["qty"] = round(g["qty"], 2)
        g["unit_price"] = price
        g["amount"] = None if price is None else round(price * g["qty"])
        lines.append(g)
    return lines
