import cv2
import numpy as np
import math


def imageFiltering(frame):
    # area of intereset(hand)
    roi = frame[y:y + h, x:x + w]

    # applying gaussian blurr to reduce the noise
    blur = cv2.GaussianBlur(roi, (5, 5), 0)
    # converting from coloured to HSV
    hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)

    # applying a mask which makes skin color white and others black
    # mask = cv2.inRange(hsv, np.array([2, 50, 50]), np.array([20, 255, 255]))
    # tạo mask vùng da tay
    mask = cv2.inRange(hsv, lower_skin, upper_skin)

    # Morphological operations to remove noise and fill holes
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.erode(mask, kernel, iterations=1)  # Remove small noise
    mask = cv2.dilate(mask, kernel, iterations=2)  # Fill holes
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)  # Close small gaps
    
    # reducing noise
    filtered = cv2.GaussianBlur(mask, (3, 3), 0)
    ret, thresh = cv2.threshold(filtered, 127, 255, 0)  # thesholding the image
    
    # finding contours in the image. Will be used later in complex hull algorithm
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filter contours by area to remove small noise
    min_area = 1000  # Minimum area for hand contour
    contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]

    return roi, thresh, contours


cap = cv2.VideoCapture(0)

# dimensions of the box
x = 100
y = 100
w = 200
h = 300  # Increased height for better hand detection
sample_rect = (350, 100, 40, 40)  # vùng lớn hơn để lấy mẫu da (x, y, w, h)
lower_skin = np.array([2, 50, 50])
upper_skin = np.array([20, 255, 255])

while True:
    ret, frame = cap.read()  # read video frame by frame
    # create a rectangle around roi
    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # Vẽ vùng lấy mẫu màu da
    sx, sy, sw, sh = sample_rect
    cv2.rectangle(frame, (sx, sy), (sx + sw, sy + sh), (255, 0, 0), 2)
    cv2.putText(frame, "Press 's' to sample skin", (sx - 50, sy - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    roi, thresh, contours = imageFiltering(frame)  # getting the filtered image

    # blank image which will be used to show the contours and defects
    drawing = np.zeros(roi.shape, np.uint8)
    try:
        # finding contour with max area
        if len(contours) == 0:
            raise ValueError("No contours found")
            
        contour = max(contours, key=lambda x: cv2.contourArea(x))
        
        # Additional check: ensure contour is large enough to be a hand
        if cv2.contourArea(contour) < 2000:
            raise ValueError("Contour too small")

        # convex hull. This creates a convex polygon.
        hull = cv2.convexHull(contour)

        # draw contours
        cv2.drawContours(drawing, [contour], -1, (0, 0, 255), 0)
        cv2.drawContours(drawing, [hull], -1, (0, 255, 255), 0)

        # finding defects in the convex polygon formed using convex hull algorithm
        hull = cv2.convexHull(contour, returnPoints=False)
        defects = cv2.convexityDefects(contour, hull)

        count_defects = 0  # defaults initially set to 0

        # finding defects and displaying them on the image
        for i in range(defects.shape[0]):
            s, e, f, d = defects[i, 0]  # defect returns 4 arguments
            # using start, end, far to find the defects location
            start = tuple(contour[s][0])
            end = tuple(contour[e][0])
            far = tuple(contour[f][0])

            # finding the angle of the defect using cosine law
            # a = math.sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2)
            # b = math.sqrt((far[0] - start[0]) ** 2 + (far[1] - start[1]) ** 2)
            # c = math.sqrt((end[0] - far[0]) ** 2 + (end[1] - far[1]) ** 2)
            # Tính góc giữa các ngón tay
            a = math.dist(start, end)
            b = math.dist(start, far)
            c = math.dist(end, far)
            angle = math.degrees(math.acos((b ** 2 + c ** 2 - a ** 2) / (2 * b * c)))
            # angle = (math.acos((b ** 2 + c ** 2 - a ** 2) / (2 * b * c)) * 180) / 3.14

            # we know, angle between 2 fingers is within 90 degrees.
            # so anything greater than that isnot considered
            if angle <= 90:
                count_defects += 1
                cv2.circle(drawing, far, 5, [0, 0, 255], -1)  # displaying defect

            cv2.line(drawing, start, end, [0, 255, 0], 2)

        if count_defects == 0:
            cv2.putText(frame, "ONE", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2)
        elif count_defects == 1:
            cv2.putText(frame, "TWO", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2)
        elif count_defects == 2:
            cv2.putText(frame, "THREE", (5, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2)
        elif count_defects == 3:
            cv2.putText(frame, "FOUR", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2)
        elif count_defects == 4:
            cv2.putText(frame, "FIVE", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2)
        else:
            pass

    except:
        pass
    # displaying result
    cv2.imshow("thresh", thresh)
    cv2.imshow("drawing", drawing)
    cv2.imshow("img", frame)

    k = cv2.waitKey(30) & 0xff  # exit if Esc is pressed
    if k == 27:
        break
    elif k == ord('s'):
        # Lấy mẫu màu da trong vùng sample
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        roi_sample = hsv[sy:sy + sh, sx:sx + sw]
        
        # Sử dụng median thay vì mean để giảm ảnh hưởng của nhiễu
        h_median = np.median(roi_sample[:, :, 0])
        s_median = np.median(roi_sample[:, :, 1])
        v_median = np.median(roi_sample[:, :, 2])
        
        # Tính standard deviation để điều chỉnh range động
        h_std = np.std(roi_sample[:, :, 0])
        s_std = np.std(roi_sample[:, :, 1])
        v_std = np.std(roi_sample[:, :, 2])
        
        # Sử dụng khoảng hẹp hơn và dựa trên độ phân tán thực tế
        h_range = max(10, min(h_std * 2, 15))  # Giới hạn từ 10-15
        s_range = max(30, min(s_std * 2, 50))  # Giới hạn từ 30-50
        v_range = max(30, min(v_std * 2, 60))  # Giới hạn từ 30-60

        lower_skin = np.array([
            max(h_median - h_range, 0), 
            max(s_median - s_range, 50),  # S tối thiểu 50 để tránh màu xám
            max(v_median - v_range, 50)   # V tối thiểu 50 để tránh vùng tối
        ], dtype=np.uint8)
        
        upper_skin = np.array([
            min(h_median + h_range, 179), 
            min(s_median + s_range, 255), 
            min(v_median + v_range, 255)
        ], dtype=np.uint8)

        print("Skin color updated:")
        print("Lower:", lower_skin, " | Upper:", upper_skin)
        print(f"HSV Median: H={h_median:.1f}, S={s_median:.1f}, V={v_median:.1f}")
        print(f"Ranges used: H±{h_range:.1f}, S±{s_range:.1f}, V±{v_range:.1f}")

cap.release()  # release the webcam
cv2.destroyAllWindows()  # destroy the window