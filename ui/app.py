import io

import api_client
import streamlit as st
from components.drawing_view import draw_boxes
from file_kind import SUPPORTED_TYPES, choose_branch, classify_file
from PIL import Image
from sample_data import LOW_CONFIDENCE, SAMPLE_CANVAS, scale_bbox

st.set_page_config(page_title="CAD2BOM", layout="wide")
st.title("CAD2BOM")
note = "Bản demo. Dữ liệu và khung nhận diện là minh họa, không phải kết quả thật."
st.caption(note if api_client.USE_MOCK else "Bản demo.")

LABEL = {"cad": "Nhánh CAD", "image": "Nhánh ảnh", None: "Chưa xác định"}
IMAGE_EXT = (".png", ".jpg", ".jpeg")
ss = st.session_state
ss.setdefault("result", None)  # {"elements", "lines", "branch"}
ss.setdefault("run_id", 0)  # đổi để reset lựa chọn trong bảng
ss.setdefault("sig", None)


def selected_rows() -> list[int]:
    """Dòng BOM đang chọn (đọc từ lần chạy trước, vì bảng nằm bên phải còn ảnh bên trái)."""
    state = ss.get(f"bom_{ss.run_id}")
    try:
        return list(state["selection"]["rows"]) if state else []
    except (KeyError, TypeError):
        return []


left, right = st.columns(2, gap="large")

# ---------- Trái: tải bản vẽ và xem ảnh ----------
with left:
    st.subheader("Bản vẽ")
    files = st.file_uploader(
        "Kéo thả DWG, DXF, PDF, PNG, JPG", type=SUPPORTED_TYPES, accept_multiple_files=True
    )
    kinds = []
    for f in files or []:
        pdf_kind = None
        if f.name.lower().endswith(".pdf"):
            pick = st.radio(
                f"{f.name} là PDF loại nào?",
                ["Chưa chọn", "Vector", "Scan"],
                horizontal=True,
                key=f"pdf-{f.name}",
            )
            pdf_kind = {"Vector": "vector", "Scan": "scan"}.get(pick)
        kinds.append(classify_file(f.name, pdf_kind))

    branch = choose_branch(kinds)
    sig = tuple((f.name, f.size) for f in files or [])
    if sig != ss.sig:  # tải file khác thì bỏ kết quả cũ
        ss.sig, ss.result = sig, None
        ss.run_id += 1

    send_files = [f for f, k in zip(files or [], kinds, strict=True) if k.branch == branch]
    image_file = next((f for f in send_files if f.name.lower().endswith(IMAGE_EXT)), None)

    if kinds:
        if branch is None:
            st.info("Chưa chọn được nhánh. Hãy xác nhận loại PDF.")
        else:
            st.success(f"{LABEL[branch]} → `POST {api_client.BRANCH_ENDPOINTS[branch]}`")
        if any(k.name.lower().endswith(".dwg") for k in kinds):
            st.warning("DWG cần converter, giấy phép chưa chốt. Nhánh CAD hiện chỉ đảm bảo DXF.")

    if image_file:
        image = Image.open(io.BytesIO(image_file.getvalue()))
        boxes, highlight = [], set()
        if ss.result:
            boxes = [
                {
                    **e,
                    "bbox": scale_bbox(e["bbox"], image.size) if api_client.USE_MOCK else e["bbox"],
                }
                for e in ss.result["elements"]
            ]
            rows = selected_rows()
            if rows and rows[0] < len(ss.result["lines"]):
                highlight = set(ss.result["lines"][rows[0]]["source_ids"])
        st.image(draw_boxes(image, boxes, highlight), use_container_width=True)
        if highlight:
            st.caption("Khung đỏ: phần tử của dòng BOM đang chọn (khung mô phỏng).")
    elif send_files:
        st.info(
            "Không có ảnh để xem trước (file CAD hoặc PDF). Thông tin phần tử xem ở bảng bên phải."
        )

# ---------- Phải: BOM ----------
with right:
    st.subheader("BOM")
    if st.button("Hiển thị BOM", type="primary", disabled=not send_files or branch is None):
        send = [(f.name, f.getvalue(), f.type or "application/octet-stream") for f in send_files]
        with st.status("Đang phân tích...", expanded=True) as status:
            bar = st.progress(0.0, text="Đang gửi bản vẽ")
            try:
                job = api_client.upload(branch, send)
                for ev in api_client.stream_job(job["job_id"], branch):
                    if ev["status"] == "failed":
                        raise RuntimeError(ev.get("error") or "Job lỗi")
                    bar.progress(ev["progress"], text=ev["step"])
                elements, lines = api_client.get_result(job["drawing_id"], branch)
            except Exception as exc:  # noqa: BLE001 - hiển thị mọi lỗi cho người dùng
                status.update(label="Lỗi", state="error")
                st.error(f"Không phân tích được: {exc}")
                st.stop()
            status.update(label="Phân tích xong", state="complete", expanded=False)
        ss.result = {"elements": elements, "lines": lines, "branch": branch}
        ss.run_id += 1

    if ss.result:
        lines, elements = ss.result["lines"], ss.result["elements"]
        table = [
            {
                "Hạng mục": ln["class"],
                "Quy cách": ln["spec"],
                "SL": ln["qty"],
                "ĐVT": ln["unit"],
                "Đơn giá": ln["unit_price"],
                "Thành tiền": ln["amount"],
            }
            for ln in lines
        ]
        st.caption("Chọn một dòng để xem thông tin và khung nhận diện trên ảnh.")
        event = st.dataframe(
            table,
            hide_index=True,
            use_container_width=True,
            on_select="rerun",
            selection_mode="single-row",
            key=f"bom_{ss.run_id}",
        )
        no_price = [f"{ln['class']} {ln['spec']}" for ln in lines if ln["unit_price"] is None]
        if no_price:
            st.warning("Dòng chưa có giá: " + ", ".join(no_price))

        rows = event.selection.rows
        if rows:
            line = lines[rows[0]]
            by_id = {e["id"]: e for e in elements}
            st.markdown(f"**{line['class']} {line['spec']}** — {line['qty']} {line['unit']}")
            detail = []
            for sid in line["source_ids"]:
                e = by_id[sid]
                detail.append(
                    {
                        "ID": sid,
                        "Handle": e.get("handle") or "(ảnh, không có)",
                        "Confidence": e["confidence"],
                        "Bbox": str(e["bbox"]),
                        "Cần rà soát": e["confidence"] < LOW_CONFIDENCE,
                    }
                )
            st.dataframe(detail, hide_index=True, use_container_width=True)
            if ss.result["branch"] == "image":
                st.caption("Nhánh ảnh là ước lượng, confidence thấp hơn nhánh CAD.")
            if api_client.USE_MOCK:
                st.caption(f"Bbox mô phỏng trên khung {SAMPLE_CANVAS[0]}x{SAMPLE_CANVAS[1]}.")
