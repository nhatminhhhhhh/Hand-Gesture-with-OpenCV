# PHÁT HIỆN, ĐẾM SỐ LƯỢNG NGÓN TAY BẰNG OPENCV  

Project này sẽ xây dựng các thuật toán để có thể detect và đếm số lượng ngón tay với OPENCV.  
## HOW TO USE  
### Sampling skin  
Khi chạy chương trình, một cửa sổ sẽ hiển thị hình ảnh từ camera, trong cửa sổ sẽ hiển thị 9 ô chữ nhật có viền xanh ở chính giữa cửa sổ.  
Ta sẽ đưa bàn tay vào 9 khung và lấy mẫu màu da ở cả 2 mặt bàn tay (lòng bàn tay và mu bàn tay). Nhấn "z" để chương trình lấy mẫu màu da.  
Khi chương trình đã lấy mẫu xong, cửa sổ "thresh" và "drawing" sẽ được mở lên.   
Cửa sổ "thresh" sẽ hiển thị frame ảnh phân đoạn bàn tay (nơi nào được nhận định là bàn tay sẽ là màu trắng, còn lại là màu đen)  
Cửa sổ "drawing" sẽ hiển thị viền contour và convex hull của ảnh phân đoạn từ "thresh", các defects biểu thị cho điểm khuyết thoả các điều kiện sẽ được biểu diễn là chấm tròn màu đó (mỗi 1 chấm tròn tương ứng với 2 ngón tay)  
