# PHÁT HIỆN, ĐẾM SỐ LƯỢNG NGÓN TAY BẰNG OPENCV  

Project này sẽ xây dựng các thuật toán để có thể detect và đếm số lượng ngón tay với OPENCV.  
## HOW TO USE  
### Sampling skin  
Khi chạy chương trình, một cửa sổ sẽ hiển thị hình ảnh từ camera, trong cửa sổ sẽ hiển thị 9 ô chữ nhật có viền xanh ở chính giữa cửa sổ.  
Ta sẽ đưa bàn tay vào 9 khung và lấy mẫu màu da ở cả 2 mặt bàn tay (lòng bàn tay và mu bàn tay). Nhấn "z" để chương trình lấy mẫu màu da.  
Khi chương trình đã lấy mẫu xong, cửa sổ "thresh" và "drawing" sẽ được mở lên.   
Cửa sổ "thresh" sẽ hiển thị frame ảnh phân đoạn bàn tay (nơi nào được nhận định là bàn tay sẽ là màu trắng, còn lại là màu đen).  
Cửa sổ "drawing" sẽ hiển thị viền contour và convex hull của ảnh phân đoạn từ "thresh", các defects biểu thị cho điểm khuyết thoả các điều kiện sẽ được biểu diễn là chấm tròn màu đó (mỗi 1 chấm tròn tương ứng với 2 ngón tay).  

### CONFIG ADJUSTMENT  
- 'CROP_REGION': (Y_start, Y_end, X_start, X_end) toạ độ khung ROI cần cắt từ camera
- 'CALIBRATION_BOXES': 9 | số lượng ô chữ nhật để lấy mẫu
- 'BOX_SIZE': 30 | kích thước của ô lấy mẫu
- 'HSV_OFFSETS': {
        'H_LOW': (offset), 'H_HIGH': (offset),
        'S_LOW': (offset), 'S_HIGH': (offset),
        'V_LOW': (offset), 'V_HIGH': (offset)
    }, | thông số để hiệu chỉnh khi lấy mẫu bằng HSV
- 'YCRCB_OFFSETS': {
  'Y_LOW': 20, 'Y_HIGH': 20,
  'Cr_LOW': 20, 'Cr_HIGH': 20,
  'Cb_LOW': 20, 'Cb_HIGH': 20
  }, | thông số để hiệu chỉnh khi lấy mẫu bằng YCrCB
- 'MIN_HAND_AREA': 1000,
  'MAX_HAND_AREA_RATIO': 0.8,
  'MIN_ASPECT_RATIO': 0.5,
  'EDGE_MARGIN': 5,
  'MIN_CENTROID_HEIGHT_RATIO': 0.1, | thông số cho việc xác định có phải là bàn tay hay không
- 'ANGLE_RANGE': (25, 80),  # Degrees for valid finger valley
  'DEFECT_DEPTH_THRESHOLD': 10000,  # Minimum depth for valley
  'MIN_FINGERTIP_DIST': 70,  # Min distance from centroid to fingertip
  'MIN_ONE_FINGER_DIST': 120,  # Min distance for ONE finger detection
- 'MORPH_KERNEL_SIZE': (4, 4),
  'MORPH_ITERATIONS': 2, | thông số cho việc open của thresh bàn tay (giảm nhiễu)


