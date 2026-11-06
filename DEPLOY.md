# Deploy lên Render (free, link 24/7)

Repo đã có sẵn `render.yaml`, `requirements.txt` (kèm gunicorn) nên Render tự hiểu cách chạy.

## Bước 1 — Đưa code lên GitHub
Tạo 1 repo trống trên https://github.com/new (ví dụ tên `tra-cuu-cuoc`), **không** tick thêm README.
Sau đó tại thư mục `C:\demo` chạy (thay `<USER>` và tên repo cho đúng):

```powershell
git branch -M main
git remote add origin https://github.com/<USER>/tra-cuu-cuoc.git
git push -u origin main
```

> Nếu đã có GitHub CLI: `gh repo create tra-cuu-cuoc --public --source=. --push`

## Bước 2 — Deploy trên Render
1. Vào https://render.com → đăng nhập bằng GitHub (free).
2. Bấm **New +** → **Blueprint** (Render sẽ đọc `render.yaml`).
   - Chọn repo vừa push → **Apply**.
   - (Hoặc **New + → Web Service**, chọn repo, Render tự nhận:
     Build = `pip install -r requirements.txt`,
     Start = `gunicorn app:app --bind 0.0.0.0:$PORT`.)
3. Đợi build ~1–2 phút. Xong có link dạng:
   **https://tra-cuu-cuoc-van-chuyen.onrender.com**

## Bước 3 — Gửi sếp
Copy link đó gửi sếp. Trang tự nạp sẵn `sample.csv`; sếp có thể bấm **Nhập dữ liệu** để thử CSV khác.

## Lưu ý gói free
- Dịch vụ "ngủ" sau ~15 phút không ai truy cập → lần mở kế tiếp chờ **~30–50 giây** rồi chạy bình thường.
- Dữ liệu import lưu trong RAM, khi dịch vụ restart sẽ quay về `sample.csv` (đúng cho demo).

## Cập nhật sau này
Chỉ cần `git push`, Render tự build lại và cập nhật link.
