# Hướng Dẫn Chạy Chương Trình

## ❌ Lỗi: `ModuleNotFoundError: No module named 'cv2'`

### Nguyên nhân:
Bạn đang chạy **Python system** thay vì **Python trong virtual environment** (.venv).

---

## ✅ Cách Khắc Phục

### Phương án 1: Dùng file .bat (Khuyến nghị - Dễ nhất!)

#### Chạy với Histogram (Tốt hơn):
```powershell
# Double-click hoặc chạy:
.\run_histogram.bat
```

#### Chạy với HSV Range (Cũ):
```powershell
# Double-click hoặc chạy:
.\run_hsv.bat
```

---

### Phương án 2: Kích hoạt Virtual Environment

```powershell
# Bước 1: Kích hoạt venv
.\.venv\Scripts\Activate.ps1

# Bước 2: Chạy chương trình
python main.py --use-histogram
# hoặc
python main.py
```

**Lưu ý:** Nếu gặp lỗi "running scripts is disabled", chạy:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### Phương án 3: Chạy trực tiếp với đường dẫn đầy đủ

```powershell
# Histogram mode
D:\Nam_3\Xu_ly_anh\.venv\Scripts\python.exe main.py --use-histogram

# HSV mode
D:\Nam_3\Xu_ly_anh\.venv\Scripts\python.exe main.py

# Custom options
D:\Nam_3\Xu_ly_anh\.venv\Scripts\python.exe main.py --use-histogram --smoothing 8 --roi-height 350
```

---

## 📝 Các Tùy Chọn Có Sẵn

```powershell
# Xem tất cả tùy chọn
D:\Nam_3\Xu_ly_anh\.venv\Scripts\python.exe main.py --help

# Ví dụ:
--camera 0              # Camera index (0, 1, 2...)
--roi-x 100             # X coordinate
--roi-y 100             # Y coordinate
--roi-width 200         # Width
--roi-height 300        # Height
--smoothing 5           # Gesture smoothing frames
--use-histogram         # Use histogram backprojection
```

---

## 🎯 So Sánh 2 Chế Độ

| Feature | HSV Range | Histogram |
|---------|-----------|-----------|
| Lệnh | `.\run_hsv.bat` | `.\run_histogram.bat` |
| Lấy mẫu | Nhấn 's' | Nhấn 'z' |
| Vùng mẫu | 1 ô vuông 40×40 | 9 ô vuông 10×10 |
| Độ chính xác | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Thích ứng ánh sáng | ❌ | ✅ |
| Tốc độ | Nhanh hơn | Hơi chậm |

---

## 🐛 Khắc Phục Lỗi Khác

### Lỗi: Camera không mở được
```powershell
# Thử camera khác
D:\Nam_3\Xu_ly_anh\.venv\Scripts\python.exe main.py --camera 1
```

### Lỗi: Không phát hiện tay
1. Nhấn 's' (HSV mode) hoặc 'z' (Histogram mode) để lấy mẫu lại
2. Điều chỉnh ánh sáng phòng
3. Đảm bảo tay ở trong khung xanh lá

### Lỗi: Phát hiện sai số ngón
1. Kiểm tra cửa sổ "thresh" - tay phải hiển thị trắng hoàn toàn
2. Lấy mẫu màu da lại
3. Thử tăng smoothing: `--smoothing 8`

---

## 📦 Cấu Trúc Project

```
d:\Nam_3\Xu_ly_anh\
├── main.py              # Code chính
├── test.py              # Code mẫu (histogram)
├── run_histogram.bat    # Chạy với histogram (mới)
├── run_hsv.bat          # Chạy với HSV (cũ)
├── README_HISTOGRAM.md  # Hướng dẫn chi tiết
├── .venv\               # Virtual environment
│   └── Scripts\
│       └── python.exe   # Python trong venv
└── saved_masks\         # Thư mục lưu masks
```

---

**Khuyến nghị:** Sử dụng `run_histogram.bat` để có kết quả tốt nhất! 🎯
