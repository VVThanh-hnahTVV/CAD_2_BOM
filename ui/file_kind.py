"""Xác định loại file người dùng tải lên để chọn nhánh xử lý (CAD hay ảnh)."""

from dataclasses import dataclass
from pathlib import PurePath

CAD_EXT = {".dwg", ".dxf"}
IMAGE_EXT = {".png", ".jpg", ".jpeg"}
PDF_EXT = {".pdf"}
SUPPORTED_TYPES = ["dwg", "dxf", "pdf", "png", "jpg", "jpeg"]


@dataclass(frozen=True)
class FileKind:
    name: str
    branch: str | None  # "cad", "image", hoặc None nếu chưa xác định được
    reason: str


def classify_file(name: str, pdf_kind: str | None = None) -> FileKind:
    """pdf_kind: "vector" hoặc "scan", do người dùng xác nhận. PDF chưa tự phân biệt được."""
    ext = PurePath(name).suffix.lower()
    if ext in CAD_EXT:
        return FileKind(name, "cad", "File CAD gốc (DWG/DXF)")
    if ext in IMAGE_EXT:
        return FileKind(name, "image", "File ảnh")
    if ext in PDF_EXT:
        if pdf_kind == "vector":
            return FileKind(name, "cad", "PDF vector (người dùng xác nhận)")
        if pdf_kind == "scan":
            return FileKind(name, "image", "PDF scan (người dùng xác nhận)")
        return FileKind(name, None, "PDF: chưa phân biệt được vector hay scan, cần xác nhận")
    return FileKind(name, None, "Định dạng chưa hỗ trợ")


def choose_branch(kinds: list[FileKind]) -> str | None:
    """Có cả hai dạng thì ưu tiên nhánh CAD. Còn PDF chưa xác nhận thì chưa chọn được."""
    branches = {k.branch for k in kinds}
    if "cad" in branches:
        return "cad"
    if "image" in branches and all(k.branch for k in kinds):
        return "image"
    return None
