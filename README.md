# TRA CỨU CƯỚC VẬN CHUYỂN — Demo (Python + Flask)

Web demo mô phỏng giao diện mẫu Canva (OCEAN FREIGHT · 2026):
https://snake-rsly1p.my.canva.site/

Cho phép **import file CSV** làm dữ liệu và **tra cứu theo nhiều trường** (logic **AND**).

## Giao diện (theo mẫu)
- **Hero**: `OCEAN FREIGHT · 2026` / `TRA CỨU CƯỚC VẬN CHUYỂN` / tagline.
- **Bộ lọc tra cứu** gồm 8 trường:
  1. Cảng đi (POL)
  2. Cảng đến (POD)
  3. Quốc gia
  4. Hãng vận chuyển
  5. Đơn vị giao nhận
  6. Tháng khởi hành
  7. Điều kiện giao hàng
  8. Giá tối đa / container
  - Nút **Tra cứu giá** và **Xóa bộ lọc**.
- **Kết quả tra cứu**: bảng 10 cột CẢNG ĐI · CẢNG ĐẾN · QUỐC GIA · HÃNG TÀU · ĐƠN VỊ ·
  THÁNG · THỜI GIAN · ĐIỀU KIỆN · THÔNG TIN · GIÁ THAM KHẢO.
- Màu theo mẫu: navy/teal (`#06446b`, `#176788`), nền mint (`#e6f1f5`), nhấn coral (`#c8475f`).

## Logic tra cứu (AND)
- 4 trường chữ (POL, POD, hãng vận chuyển, đơn vị giao nhận): khớp **chuỗi con**, không phân biệt hoa/thường.
- **Giá tối đa / container**: lọc **số**, giữ các dòng có cước `<=` giá nhập (tự bỏ ký tự "USD", dấu phẩy…).
- Dòng kết quả phải thỏa **tất cả** điều kiện đã nhập. Ô trống thì bỏ qua.

## Import CSV
- Nhận file `.csv`, tự xử lý BOM, tự dò dấu phân tách (`,` `;` tab `|`).
- Cột CSV được ánh xạ sang schema qua alias (xem `COLUMN_ALIASES` trong `app.py`),
  nên vẫn chạy nếu header đặt tên hơi khác. Dùng `sample.csv` làm chuẩn.

## Cài đặt & chạy
```powershell
cd C:\demo
pip install -r requirements.txt
python app.py
```
Mở: http://127.0.0.1:5000 (trang tự nạp sẵn `sample.csv` để xem ngay).

## Thử nhanh
- `Cảng đi = Cát Lái` + `Hãng vận chuyển = ONE` → tuyến HCM–Shanghai.
- `Giá tối đa = 800` → chỉ các tuyến cước ≤ 800 USD.
- `Cảng đến = Singapore` + `Giá tối đa = 800` → tuyến Đà Nẵng–Singapore.

## Ghi chú
- Dữ liệu lưu trong bộ nhớ tiến trình (demo) — restart server sẽ nạp lại `sample.csv`.
- Đổi `app.secret_key` nếu triển khai thật.
