# Dự án Dịch thuật Game Where Winds Meet (WWM) sang tiếng Việt

Dự án này sử dụng AI (Google Gemini) để tự động dịch các file ngôn ngữ của game Where Winds Meet từ tiếng Trung sang tiếng Việt.

## 📂 Cấu trúc kho lưu trữ
- `gemini_translate.py`: Script chính để thực hiện dịch thuật bằng AI.
- `translation_vn.tsv`: File chứa kết quả dịch thuật (định dạng ID - Nội dung).
- `requirements.txt`: Danh sách các thư viện cần thiết.

## 🚀 Cách sử dụng đơn giản (Dành cho người không chuyên)

### Bước 1: Chuẩn bị
1. Cài đặt Python trên máy tính của bạn.
2. Mở thư mục này trong Terminal/Command Prompt.
3. Cài đặt thư viện cần thiết bằng lệnh:
   ```bash
   pip install -r requirements.txt
   ```

### Bước 2: Chạy dịch thuật
Chỉ cần chạy lệnh sau:
```bash
python gemini_translate.py
```
Script sẽ tự động đọc file văn bản đã trích xuất và dùng AI để dịch sang tiếng Việt.

## 🛠 Tùy chỉnh
Bạn có thể mở file `gemini_translate.py` để thay đổi:
- `API_KEY`: Mã API của bạn.
- `limit`: Số lượng dòng muốn dịch (mặc định đang để thử nghiệm 100 dòng).

---
*Dự án được hỗ trợ bởi Manus AI.*
