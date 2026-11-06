"""
Web demo: TRA CỨU CƯỚC VẬN CHUYỂN (Ocean Freight)
Giao diện mô phỏng theo mẫu Canva: https://snake-rsly1p.my.canva.site/

Chức năng:
  - Import file CSV đóng vai trò dữ liệu tra cứu.
  - Bộ lọc tra cứu theo nhiều trường, logic AND:
        Cảng đi (POL), Cảng đến (POD), Hãng vận chuyển,
        Đơn vị giao nhận, Giá tối đa / container.

Chạy:
    pip install -r requirements.txt
    python app.py
Mở http://127.0.0.1:5000
"""

import csv
import io
import os
import re

from flask import Flask, flash, redirect, render_template, request, url_for

app = Flask(__name__)
app.secret_key = "demo-secret-key-change-me"

# --------------------------------------------------------------------------
# Cấu hình cột dữ liệu (khớp mẫu thiết kế)
# key nội bộ  ->  nhãn hiển thị (tiêu đề cột, viết HOA theo mẫu)
# --------------------------------------------------------------------------
DISPLAY_HEADERS = {
    "pol": "CẢNG ĐI",
    "pod": "CẢNG ĐẾN",
    "quoc_gia": "QUỐC GIA",
    "carrier": "HÃNG TÀU",
    "forwarder": "ĐƠN VỊ",
    "thang": "THÁNG",
    "thoi_gian": "THỜI GIAN",
    "thong_tin": "THÔNG TIN",
    "gia_tham_khao": "GIÁ THAM KHẢO",
}

# Cột không hiển thị trong bảng kết quả (dù CSV có chứa).
HIDDEN_COLUMNS = {"dieu_kien"}

# Thứ tự cột mong muốn khi hiển thị bảng kết quả.
PREFERRED_ORDER = list(DISPLAY_HEADERS.keys())

# Các bí danh (alias) tên cột trong CSV -> key nội bộ.
# Giúp app vẫn chạy nếu header CSV đặt tên khác nhau.
COLUMN_ALIASES = {
    "pol": {"pol", "cang_di", "cảng đi", "cang di", "port of loading", "origin"},
    "pod": {"pod", "cang_den", "cảng đến", "cang den", "port of discharge", "destination"},
    "quoc_gia": {"quoc_gia", "quốc gia", "quoc gia", "country", "nuoc"},
    "carrier": {"carrier", "hang_tau", "hãng tàu", "hang tau", "hang_van_chuyen", "line"},
    "forwarder": {"forwarder", "don_vi", "đơn vị", "don vi", "don_vi_giao_nhan", "đơn vị giao nhận", "agent"},
    "thang": {"thang", "tháng", "thang_khoi_hanh", "tháng khởi hành", "month", "etd"},
    "thoi_gian": {"thoi_gian", "thời gian", "thoi gian", "transit", "transit_time", "transit time"},
    "dieu_kien": {"dieu_kien", "điều kiện", "dieu_kien_giao_hang", "điều kiện giao hàng", "terms", "incoterms"},
    "thong_tin": {"thong_tin", "thông tin", "thong tin", "note", "ghi_chu", "info"},
    "gia_tham_khao": {"gia_tham_khao", "giá tham khảo", "gia tham khao", "price", "gia", "cuoc", "reference_price"},
}

# --------------------------------------------------------------------------
# Các trường của bộ lọc tra cứu (đúng theo mẫu Canva)
#   id    : tên tham số trên URL / form
#   label : nhãn hiển thị
#   column: key cột nội bộ dùng để so khớp
#   type  : 'text'  -> khớp chuỗi con (contains), không phân biệt hoa/thường
#           'max'   -> lọc số: giữ dòng có giá trị <= số nhập
# --------------------------------------------------------------------------
FILTER_FIELDS = [
    {"id": "pol", "label": "Cảng đi (POL)", "column": "pol", "type": "select"},
    {"id": "pod", "label": "Cảng đến (POD)", "column": "pod", "type": "select"},
    {"id": "quoc_gia", "label": "Quốc gia", "column": "quoc_gia", "type": "select"},
    {"id": "carrier", "label": "Hãng vận chuyển", "column": "carrier", "type": "select"},
    {"id": "forwarder", "label": "Đơn vị giao nhận", "column": "forwarder", "type": "select"},
    {"id": "thang", "label": "Tháng khởi hành", "column": "thang", "type": "select"},
]

# --------------------------------------------------------------------------
# Các mục (tab) của khu tra cứu — theo thiết kế gốc.
#   ready = True  : đã có chức năng (hiện chỉ "Cước xuất khẩu").
#   ready = False : khung rỗng, sẽ cập nhật chức năng sau.
# --------------------------------------------------------------------------
TABS = [
    {"id": "cuoc_xuat_khau", "label": "Cước xuất khẩu", "ready": True},
    {"id": "cho_cho_xac_nhan", "label": "Chỗ chờ xác nhận", "ready": False},
    {"id": "phi_huy", "label": "Phí hủy", "ready": False},
    {"id": "chung_tu", "label": "Chứng từ", "ready": False},
    {"id": "dieu_kien", "label": "Điều kiện", "ready": False},
]
DEFAULT_TAB = "cuoc_xuat_khau"

# Dữ liệu đang tải (bộ nhớ tiến trình, phục vụ demo).
DATA: list[dict] = []
COLUMNS: list[str] = []          # key nội bộ, theo thứ tự hiển thị
SOURCE_NAME: str = ""

ALLOWED_EXTENSIONS = {".csv"}
SAMPLE_PATH = os.path.join(os.path.dirname(__file__), "sample.csv")


# --------------------------------------------------------------------------
# Tiện ích
# --------------------------------------------------------------------------
def _norm(s: str) -> str:
    return (s or "").strip().lower()


def map_header_to_key(header: str) -> str:
    """Ánh xạ 1 tên cột CSV sang key nội bộ nếu khớp alias; nếu không giữ nguyên."""
    h = _norm(header)
    for key, aliases in COLUMN_ALIASES.items():
        if h in {_norm(a) for a in aliases}:
            return key
    return header.strip()


def to_number(value) -> float | None:
    """Trích số từ chuỗi như '1,850 USD' -> 1850.0. Không có số -> None."""
    if value is None:
        return None
    digits = re.sub(r"[^\d.]", "", str(value).replace(",", ""))
    if digits in ("", "."):
        return None
    try:
        return float(digits)
    except ValueError:
        return None


def allowed_file(filename: str) -> bool:
    return os.path.splitext(filename.lower())[1] in ALLOWED_EXTENSIONS


def parse_csv(file_bytes: bytes) -> tuple[list[str], list[dict]]:
    """Đọc CSV -> (columns[key nội bộ], rows). Xử lý BOM và tự dò delimiter."""
    try:
        text = file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = file_bytes.decode("latin-1")

    try:
        delimiter = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|").delimiter
    except csv.Error:
        delimiter = ","

    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    raw_headers = [c.strip() for c in (reader.fieldnames or [])]
    keys = [map_header_to_key(h) for h in raw_headers]

    rows = []
    for raw in reader:
        row = {}
        for raw_h, key in zip(raw_headers, keys):
            row[key] = (raw.get(raw_h, "") or "").strip()
        rows.append(row)

    # Sắp thứ tự cột: cột quen thuộc theo PREFERRED_ORDER trước, phần còn lại giữ nguyên.
    known = [k for k in PREFERRED_ORDER if k in keys]
    others = [k for k in keys if k not in PREFERRED_ORDER]
    ordered = [k for k in (known + others) if k not in HIDDEN_COLUMNS]
    return ordered, rows


def search(rows: list[dict], criteria: dict) -> list[dict]:
    """Lọc rows theo logic AND dựa trên FILTER_FIELDS.

    - type 'select': dòng phải KHỚP CHÍNH XÁC giá trị đã chọn (không phân biệt hoa/thường).
    - type 'max'   : số của ô phải <= số nhập.
    - type 'text'  : dòng phải CHỨA chuỗi tìm (không phân biệt hoa/thường).
    Mọi điều kiện đã chọn/nhập đều phải thỏa (AND). Mục để trống bị bỏ qua.
    """
    result = []
    for row in rows:
        ok = True
        for field in FILTER_FIELDS:
            raw = (criteria.get(field["id"]) or "").strip()
            if not raw:
                continue
            cell = row.get(field["column"], "")
            if field["type"] == "max":
                limit = to_number(raw)
                cell_num = to_number(cell)
                if limit is not None and (cell_num is None or cell_num > limit):
                    ok = False
                    break
            elif field["type"] == "select":
                if _norm(raw) != _norm(cell):
                    ok = False
                    break
            else:  # text contains
                if _norm(raw) not in _norm(cell):
                    ok = False
                    break
        if ok:
            result.append(row)
    return result


def build_options(rows: list[dict]) -> dict[str, list[str]]:
    """Sinh danh sách lựa chọn cho mỗi dropdown từ các giá trị có trong dữ liệu."""
    options = {}
    for field in FILTER_FIELDS:
        col = field["column"]
        values = {(r.get(col, "") or "").strip() for r in rows}
        values.discard("")
        options[field["id"]] = sorted(values, key=lambda s: s.lower())
    return options


def load_sample():
    """Nạp sẵn sample.csv khi khởi động để trang có dữ liệu minh họa."""
    global DATA, COLUMNS, SOURCE_NAME
    if os.path.exists(SAMPLE_PATH):
        with open(SAMPLE_PATH, "rb") as f:
            COLUMNS, DATA = parse_csv(f.read())
        SOURCE_NAME = "sample.csv"


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------
@app.route("/", methods=["GET"])
def index():
    current_tab = request.args.get("tab", DEFAULT_TAB)
    if current_tab not in {t["id"] for t in TABS}:
        current_tab = DEFAULT_TAB

    criteria = {f["id"]: request.args.get(f["id"], "") for f in FILTER_FIELDS}
    searched = any(v.strip() for v in criteria.values())
    results = search(DATA, criteria) if DATA else []

    return render_template(
        "index.html",
        tabs=TABS,
        current_tab=current_tab,
        filter_fields=FILTER_FIELDS,
        options=build_options(DATA),
        display_headers=DISPLAY_HEADERS,
        columns=COLUMNS,
        source_name=SOURCE_NAME,
        total=len(DATA),
        criteria=criteria,
        results=results,
        searched=searched,
    )


@app.route("/import", methods=["POST"])
def import_csv():
    global DATA, COLUMNS, SOURCE_NAME

    file = request.files.get("csv_file")
    if file is None or file.filename == "":
        flash("Chưa chọn file nào.", "error")
        return redirect(url_for("index"))
    if not allowed_file(file.filename):
        flash("Chỉ chấp nhận file .csv", "error")
        return redirect(url_for("index"))

    try:
        columns, rows = parse_csv(file.read())
    except Exception as exc:  # noqa: BLE001
        flash(f"Không đọc được file CSV: {exc}", "error")
        return redirect(url_for("index"))

    if not columns:
        flash("File CSV không có dòng tiêu đề cột.", "error")
        return redirect(url_for("index"))

    DATA, COLUMNS, SOURCE_NAME = rows, columns, file.filename
    flash(f"Đã import '{file.filename}': {len(rows)} dòng dữ liệu.", "success")
    return redirect(url_for("index"))


@app.route("/clear", methods=["POST"])
def clear():
    global DATA, COLUMNS, SOURCE_NAME
    DATA, COLUMNS, SOURCE_NAME = [], [], ""
    flash("Đã xoá dữ liệu đã import.", "success")
    return redirect(url_for("index"))


load_sample()

if __name__ == "__main__":
    app.run(debug=True)
