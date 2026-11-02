# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Dự án **CAD2BOM** (tên tạm): đọc bản vẽ CAD hoặc ảnh, ra dữ liệu có cấu trúc, tạo BOM và báo giá nháp, người duyệt rồi mới xuất Excel hoặc nhập ERP.

## Trạng thái hiện tại

- Đang ở giai đoạn đề xuất và thiết kế. **Chưa có hệ thống hay code chạy được.** Hiện chỉ có một tài liệu thiết kế dạng slide HTML: `docs/CAD2BOM_He_thong_E2E.html`.
- Mọi KPI đều là **giả thuyết**, chỉ coi là kết quả sau khi đo trong PoC: giảm công dự toán, tăng độ chính xác, bóc khối lượng còn vài phút. Proposal gốc ghi 40–50% công dự toán, tài liệu thiết kế E2E ghi 15–25%; con số chính thức chưa thống nhất với đối tác.
- Đối tượng đọc tài liệu: đối tác tư vấn (Deloitte Tohmatsu Consulting) và khách hàng ngành xây dựng. Tài liệu hiện viết bằng tiếng Việt.

## Nguyên tắc thiết kế đã chốt

Không tự ý đổi. Muốn đổi thì hỏi trước.

1. **Hai nhánh theo dạng file đầu vào.** Nhánh CAD: DWG, DXF, PDF vector. Nhánh ảnh: PNG, JPG, PDF scan. Có cả hai thì ưu tiên nhánh CAD.
2. **Nhánh CAD do code xử lý hoàn toàn, không dùng LLM.** Khi gặp layer hoặc block lạ, người duyệt mapping một lần rồi hệ thống lưu vào kho cấu hình.
3. **Nhánh ảnh dùng model nhận diện** (detect, segment, OCR). Kết quả là ước lượng, confidence thấp hơn, cần rà soát nhiều hơn.
4. **Số lượng, chiều dài, diện tích do code đếm và đo.** Model không tự đếm.
5. **Một JSON chuẩn dùng chung** cho cả hai nhánh (schema ở dưới).
6. **Mỗi giá trị truy ngược được về bản vẽ** (handle, bbox).
7. **Con người ở hai chỗ:** duyệt mục confidence thấp, và phê duyệt báo giá cuối. ERP chỉ nhập sau khi đã duyệt.
8. **Chạy trong môi trường của khách hàng.** Bản vẽ không ra ngoài.

## Từ vựng

- **BOM** (Bill of Materials): bảng kê vật tư, gồm hạng mục, quy cách, số lượng.
- **ADE** = Automated Document Extraction.
- Dùng **"AI model"**, không dùng "AI agent".
- **confidence**: độ tin cậy từ 0 đến 1. **handle**: mã entity trong file CAD. **bbox**: khung bao trên bản vẽ.
- **PoC**: chạy thử trên bản vẽ thật của khách để đo, trước khi triển khai.

## Quy trình người dùng (5 bước)

1. Tải bản vẽ (người lập dự toán). Hệ thống lưu bản gốc, tự chọn nhánh.
2. Chờ phân tích (chạy nền, xem tiến độ).
3. Rà soát: bấm một dòng thì phần tử sáng lên trên bản vẽ; duyệt hoặc sửa. Hệ thống gắn cờ mục confidence thấp, phần còn lại vào BOM tự động.
4. Xem BOM và báo giá nháp (định giá từ bảng giá của khách).
5. Phê duyệt (người phê duyệt, khác người lập). Sau đó xuất Excel hoặc nhập ERP.

Có bản vẽ sửa đổi: tải bản mới, hệ thống chỉ ra phần thay đổi, người dùng chỉ rà soát phần đó.

## Kiến trúc tổng thể

- **Ứng dụng web:** dự án và upload, màn rà soát, BOM và báo giá, phê duyệt.
- **API và điều phối:** phân quyền, hàng đợi job, thử lại khi lỗi, nhật ký kiểm toán (ai sửa, ai duyệt).
- **Dịch vụ xử lý:** nhánh CAD (đọc vector, bằng code), nhánh ảnh (detect, OCR, dùng GPU), BOM và báo giá (tổng hợp, định giá).
- **Kho dữ liệu:** kho cấu hình theo khách (mapping, quy tắc bóc tách, bảng giá), file gốc, CSDL dự án (phần tử, BOM, báo giá).
- **Hệ thống ngoài:** ERP của khách, Excel/CSV.

### Nhánh CAD (5 bước)

Đọc file → kiểm kê (layer, block, text, entity) → dựng đối tượng (gom nét rời thành tường, phòng) → phân loại và gắn thuộc tính → đếm, đo.

### Nhánh ảnh (5 bước)

Tiền xử lý (xoay, khử nhiễu, cắt tile) → detect, segment → OCR → hiệu chỉnh tỷ lệ (pixel sang mét) → đếm, đo.

## JSON chuẩn

```json
{
  "id": "D-01",
  "class": "door",
  "spec": "W800",
  "qty": 1,
  "source": "cad",
  "view": "plan_1F",
  "handle": "2F3A",
  "bbox": [412, 208, 452, 248],
  "confidence": 0.97
}
```

- Phần tử đo bằng chiều dài hoặc diện tích: thay `qty` bằng `length_m` hoặc `area_m2`.
- `id` phải ổn định để loại trùng giữa các view (mặt bằng, mặt đứng, mặt cắt).
- `source` là `cad` hoặc `image`. Nhánh ảnh để trống `handle`, `bbox` theo tọa độ ảnh.
- BOM: nhóm theo `class` và `spec`, cộng số lượng, áp quy tắc bóc tách của khách, xuất Excel hoặc CSV. Mỗi dòng giữ ID nguồn.

## Mô hình và dữ liệu (nhánh ảnh)

- Tên model là **ứng viên, chưa chốt**, phải so sánh trong PoC: YOLO, Mask R-CNN, kiểu CubiCasa5K cho detect và segment; PaddleOCR cho OCR.
- CubiCasa5K: 5.000 ảnh mặt bằng, 83 loại nhãn (huấn luyện dùng 12 loại phòng và 11 loại icon), chia 4.200/400/400. Chủ yếu nhà ở Phần Lan, nên phải bổ sung dữ liệu công trình của khách. Thiết bị như điều hòa chưa có nhãn riêng.
- Nguồn dữ liệu bổ sung: ảnh tự sinh từ CAD của khách (render rồi làm mờ, lệch, nhiễu; nhãn lấy từ entity) và ảnh scan thật có nhãn do người gán.
- **Giấy phép:** annotation của FloorPlanCAD là CC BY-NC 4.0, chỉ dùng để thử nghiệm. Dùng thương mại phải xin phép hoặc dùng dữ liệu riêng. Kiểm tra giấy phép trước khi đưa bất kỳ dataset hay công cụ nào vào sản phẩm (kể cả ODA File Converter).

## Đo lường (PoC)

- Đáp án chuẩn: bộ bóc tách của chuyên gia trên bản vẽ thật, chưa chuẩn bị trước.
- Chỉ số: tỷ lệ sót, tỷ lệ đếm trùng, độ hiệu chỉnh của confidence, thời gian xử lý, công rà soát của người.
- Đo sai số **theo từng dòng hạng mục**, không báo một con số % chung (sai số trái dấu dễ triệt tiêu nhau trên tổng tiền).
- Đo riêng từng nhánh và từng bước, không chỉ đo AI.

## Câu hỏi mở (cần khách xác nhận)

- Khách có file DWG/DXF gốc hay chủ yếu PDF và ảnh?
- Loại công trình và hạng mục ưu tiên cho BOM đầu tiên?
- Có bộ bóc tách chuẩn của chuyên gia để làm đáp án đối chứng không?
- Quy tắc bóc tách, master vật tư, hệ thống ERP đích?
- Ai trả giấy phép đọc DWG (ODA File Converter) khi sản phẩm chạy thật?

## Tài liệu đang có

- `docs/CAD2BOM_He_thong_E2E.html`: **tài liệu duy nhất cần làm việc.** Bộ slide HTML một file, `lang="vi"`, 13 phần tử `.slide` (1 cover, 1 dark, 11 thường), ảnh nhúng dạng data URI, tiêu đề "AI phân tích bản vẽ CAD → BOM". Không có từ điển dịch en/ja trong file.
- `main.py`: file mẫu mặc định của PyCharm, không phải code sản phẩm. Không dựa vào nó.

## Cách làm việc với Claude

- Trả lời bằng **tiếng Việt**. Giữ thuật ngữ kỹ thuật bằng tiếng Anh (BOM, JSON, layer, block, bbox, confidence).
- Không khẳng định hệ thống đã chạy hay số liệu đã đo khi chưa có. Dữ liệu mẫu phải ghi rõ "minh họa". Ảnh mô phỏng phải ghi rõ là mô phỏng.
- Thông số dataset, thư viện, giấy phép: tìm nguồn và dẫn nguồn, không đoán. Nói rõ phần nào là ứng viên hoặc ước tính.
- Không thêm LLM vào nhánh CAD. Không đổi các nguyên tắc ở mục "đã chốt" khi chưa được đồng ý.
- Làm đúng phạm vi được yêu cầu. Không tự thêm hay bớt slide, mục, tính năng. Phạm vi mơ hồ thì hỏi một câu ngắn.
- Khi trình bày: ít chữ, nhiều hình minh họa, sơ đồ có nhãn trên mũi tên. Không viết lặp lại nội dung đã có ở slide khác.

## Khi sửa `docs/CAD2BOM_He_thong_E2E.html`

- Sửa nhỏ thì sửa tại chỗ, không viết lại cả file. Giữ nguyên tên file và đường dẫn đã xuất bản.
- Sau mỗi thay đổi, kiểm tra: không chữ tràn khỏi slide, không lỗi console.
- Nội dung phải khớp các nguyên tắc "đã chốt" (không "AI agent", không LLM ở nhánh CAD).
- Dữ liệu demo (phần tử, confidence, đơn giá) là dữ liệu mẫu, không phải kết quả thật.

## Build và test

Dùng **uv** quản lý package (Python 3.12, một `pyproject.toml` ở gốc). Không phải git repo.

```
uv sync                                        # cài dependency
uv run uvicorn backend.app.main:app --reload   # backend, chạy từ thư mục gốc
uv run streamlit run ui/app.py                 # UI demo
uv run pytest                                  # toàn bộ test
uv run pytest backend/tests/api/test_health.py::test_health   # một test
uv run ruff check .                            # lint
uv add <gói>                                   # thêm dependency (--dev cho dev)
```

Cấu trúc: `backend/app/` (FastAPI: `api/v1` → `services` → `repositories` → `models`; `schemas`, `workers`, `config`, `core`, `db`), `backend/pipeline/` (`common`, `cad`, `image`, `bom`, chạy độc lập), `backend/eval/`, `ui/` (Streamlit, chỉ gọi API qua `ui/api_client.py`, không import `backend/`), `schema/`, `backend/config`, `data/` và `backend/storage/` (gitignore). `main.py` ở gốc là file mẫu PyCharm.
