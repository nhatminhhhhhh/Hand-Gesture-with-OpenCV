import cv2
import numpy as np

# Đọc ảnh mẫu cử chỉ
templates = {
    "STOP1": cv2.resize(cv2.imread('Source/stop/1.jpg', 0), (100, 100)),
    "STOP2": cv2.resize(cv2.imread('Source/stop/2.jpg', 0), (100, 100)),
    "STOP3": cv2.resize(cv2.imread('Source/stop/3.jpg', 0), (100, 100)),
    "STOP4": cv2.resize(cv2.imread('Source/stop/4.jpg', 0), (100, 100)),
    "STOP5": cv2.resize(cv2.imread('Source/stop/5.jpg', 0), (100, 100)),
    "STOP6": cv2.resize(cv2.imread('Source/stop/6.jpg', 0), (100, 100)),
    "STOP7": cv2.resize(cv2.imread('Source/stop/7.jpg', 0), (100, 100)),

    "FORWARD1": cv2.imread('Source/FORWARD/1.jpg', 0),
    "FORWARD2": cv2.imread('Source/FORWARD/2.jpg', 0),
    "FORWARD3": cv2.imread('Source/FORWARD/3.jpg', 0),
    "FORWARD4": cv2.imread('Source/FORWARD/4.jpg', 0),
    "FORWARD5": cv2.imread('Source/FORWARD/5.jpg', 0),
    "FORWARD6": cv2.imread('Source/foward/6.jpg', 0),
    "FORWARD7": cv2.imread('Source/FORWARD/7.jpg', 0),
    # "LEFT": cv2.imread("left.jpg", 0)

}

# Khởi tạo webcam
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Tăng cường ảnh để dễ so khớp
    gray = cv2.GaussianBlur(gray, (5,5), 0)
    gray = cv2.equalizeHist(gray)

    # Cắt vùng quan tâm (ROI)
    roi = gray[50:300, 50:300]
    _, mask = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=1)
    mask = cv2.erode(mask, kernel, iterations=1)

    cv2.rectangle(frame, (50,50), (300,300), (0,255,0), 2)

    best_score = 0
    best_action = "NONE"

    # So khớp từng mẫu
    for action, template in templates.items():
        #res = cv2.matchTemplate(roi, template, cv2.TM_CCOEFF_NORMED) # so sánh với roi là hinhf xám
        res = cv2.matchTemplate(mask, template, cv2.TM_CCOEFF_NORMED) # so sánh với hình phân đoạn
        _, max_val, _, _ = cv2.minMaxLoc(res)
        if max_val > best_score:
            best_score = max_val
            best_action = action

    # Chỉ chấp nhận nếu độ khớp > ngưỡng
    if best_score > 0.3:
        cv2.putText(frame, f"Action: {best_action}", (50, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255,0), 2)
    else:
        cv2.putText(frame, "No match", (50, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,0,255), 2)

    cv2.imshow("Frame", frame)
    cv2.imshow("ROI", roi)
    cv2.imshow("Mask", mask)
    if cv2.waitKey(1) == 27:  # ESC
        break

cap.release()
cv2.destroyAllWindows()
