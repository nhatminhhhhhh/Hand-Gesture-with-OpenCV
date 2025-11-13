# import cv2
# import numpy as np
# import math

# # Load face detector
# face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')


# def draw_skin_sample_boxes(frame):
# 	"""Vẽ 3 ô vuông dọc để lấy mẫu màu da"""
# 	frame_height, frame_width = frame.shape[:2]
	
# 	# Vị trí các ô vuông (bên phải màn hình, dọc theo chiều cao)
# 	box_size = 20  # Kích thước mỗi ô
# 	x_pos = frame_width // 5  # Vị trí X (1/5 từ trái)
	
# 	# 3 ô vuông dọc: trên, giữa, dưới
# 	boxes = [
# 		(x_pos, frame_height // 3, box_size, box_size),      # Ô trên
# 		(x_pos, frame_height // 2, box_size, box_size),      # Ô giữa  
# 		(x_pos, 2 * frame_height // 3, box_size, box_size)   # Ô dưới
# 	]
	
# 	# Vẽ các ô vuông màu tím (để dễ nhìn)
# 	for (x, y, w, h) in boxes:
# 		cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 255), 2)
	
# 	return boxes


# def calibrate_skin_color(frame, boxes):
# 	"""Lấy mẫu màu da từ 3 ô vuông và tính ngưỡng HSV"""
# 	hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
	
# 	h_values = []
# 	s_values = []
# 	v_values = []
	
# 	# Lấy mẫu từ 3 ô vuông
# 	for (x, y, w, h) in boxes:
# 		roi_sample = hsv_frame[y:y+h, x:x+w]
		
# 		# Thu thập giá trị H, S, V
# 		h_values.extend(roi_sample[:, :, 0].flatten())
# 		s_values.extend(roi_sample[:, :, 1].flatten())
# 		v_values.extend(roi_sample[:, :, 2].flatten())
	
# 	# Tính mean của tất cả samples
# 	h_mean = np.mean(h_values)
# 	s_mean = np.mean(s_values)
# 	v_mean = np.mean(v_values)
	
# 	# Tính offset như trong Handy C++ (±80 cho low, ±30 cho high)
# 	offset_low = 80
# 	offset_high = 30
	
# 	# Tạo ngưỡng HSV
# 	lower_skin = np.array([
# 		max(h_mean - offset_low, 0),
# 		max(s_mean - offset_low, 0),
# 		max(v_mean - offset_low, 0)
# 	], dtype=np.uint8)
	
# 	upper_skin = np.array([
# 		min(h_mean + offset_high, 179),
# 		min(s_mean + offset_high, 255),
# 		min(v_mean + offset_high, 255)
# 	], dtype=np.uint8)
	
# 	return lower_skin, upper_skin



# def centroid(max_contour):
# 	"""Calculate centroid of contour (for purple point tracking)"""
# 	moment = cv2.moments(max_contour)
# 	if moment['m00'] != 0:
# 		cx = int(moment['m10'] / moment['m00'])
# 		cy = int(moment['m01'] / moment['m00'])
# 		return cx, cy
# 	else:
# 		return None



# def calibrate_hull_area(thresh):
# 	"""Tính hull area từ thresh để calibrate min/max area"""
# 	try:
# 		# Find contours on thresh
# 		contours_roi, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
		
# 		if len(contours_roi) > 0:
# 			# Get largest contour
# 			contour = max(contours_roi, key=cv2.contourArea)
			
# 			# Get convex hull
# 			hull = cv2.convexHull(contour)
			
# 			# Calculate hull area
# 			hull_area = cv2.contourArea(hull)
			
# 			return hull_area
# 	except:
# 		pass
	
# 	return 0


# def imageFiltering(frame, lower_skin, upper_skin):

# 	#area of intereset(hand)
# 	roi = frame[y:y+h,x:x+w]

# 	#applying gaussian blurr to reduce the noise
# 	blur = cv2.GaussianBlur(roi,(5,5),0)
# 	#converting from coloured to HSV
# 	hsv = cv2.cvtColor(blur,cv2.COLOR_BGR2HSV)

# 	#applying a mask which makes skin color white and others black
# 	mask = cv2.inRange(hsv, lower_skin, upper_skin)

# 	kernel = np.ones((5,5))
# 	#reducing noise
# 	filtered = cv2.GaussianBlur(mask,(3,3),0)
# 	ret,thresh = cv2.threshold(filtered,127,255,0) #thesholding the image
# 	thesh = cv2.GaussianBlur(thresh,(5,5),0) #reducing the noise
# 	#finding contours in the image. Will be used later in complex hull algorithm
# 	contours,hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

# 	return roi, thresh, contours


# cap = cv2.VideoCapture(0)

# #dimensions of the box
# x = 100
# y = 100
# w = 200
# h = 200

# # Dimensions of tracking ROI (follows hand)
# track_roi_size = 150  # Size of tracking ROI box

# # Biến cho skin calibration
# calibrated = False
# lower_skin = np.array([2, 50, 50])
# upper_skin = np.array([20, 255, 255])

# # Biến cho hull area calibration
# min_hull_area = 0
# max_hull_area = float('inf')
# area_calibrated = False

# while True:
# 	ret,frame = cap.read() #read video frame by frame
	
# 	if not ret:
# 		print("Cannot read frame")
# 		break
	
# 	frame = cv2.flip(frame, 1)  # Flip horizontal
	
# 	# === HAND TRACKING ROI (Calculate position but don't draw yet) ===
# 	hand_center = None
# 	tracking_roi_rect = None
# 	distance_x = 0
# 	distance_y = 0
# 	distance_total = 0
# 	hand_mask = None
# 	track_x = 0
# 	track_y = 0
	
# 	if calibrated:
# 		# Find hand center in full frame
# 		hand_center, hand_contour, hand_mask = find_hand_center(frame, lower_skin, upper_skin)
		
# 		if hand_center is not None:
# 			cx, cy = hand_center
			
# 			# Calculate tracking ROI position (centered on hand)
# 			track_x = cx - track_roi_size // 2
# 			track_y = cy - track_roi_size // 2
			
# 			# Keep tracking ROI within frame bounds
# 			track_x = max(0, min(track_x, frame.shape[1] - track_roi_size))
# 			track_y = max(0, min(track_y, frame.shape[0] - track_roi_size))
			
# 			tracking_roi_rect = (track_x, track_y, track_roi_size, track_roi_size)
			
# 			# Calculate distance between finger detection ROI center and hand tracking ROI center
# 			finger_roi_center_x = x + w // 2
# 			finger_roi_center_y = y + h // 2
			
# 			tracking_roi_center_x = track_x + track_roi_size // 2
# 			tracking_roi_center_y = track_y + track_roi_size // 2
			
# 			# Distance (error for servo control)
# 			distance_x = tracking_roi_center_x - finger_roi_center_x
# 			distance_y = tracking_roi_center_y - finger_roi_center_y
# 			distance_total = math.sqrt(distance_x**2 + distance_y**2)
	
# 	#create a rectangle around finger detection ROI (green box)
# 	cv2.rectangle(frame,(x, y), (x+w, y+h), (0,255,0), 2)
# 	cv2.putText(frame, "Finger Detection", (x, y-10), 
# 			   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
	
# 	# Chỉ vẽ 3 ô vuông để lấy mẫu màu da khi chưa calibrate
# 	if not calibrated:
# 		sample_boxes = draw_skin_sample_boxes(frame)
# 		# Hiển thị hướng dẫn
# 		cv2.putText(frame, "Place hand in purple boxes", (10, 30),
# 					cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
# 		cv2.putText(frame, "Press 'C' to calibrate skin", (10, 60),
# 					cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
# 	elif not area_calibrated:
# 		cv2.putText(frame, "Make FIST in green box, press 'I' for min area", (10, 30),
# 					cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
# 		cv2.putText(frame, "Open 5 FINGERS, press 'A' for max area", (10, 60),
# 					cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
# 		if min_hull_area > 0:
# 			cv2.putText(frame, f"Min Area: {int(min_hull_area)}", (10, 90),
# 						cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
# 		if max_hull_area < float('inf'):
# 			cv2.putText(frame, f"Max Area: {int(max_hull_area)}", (10, 120),
# 						cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
# 	else:
# 		cv2.putText(frame, "Calibrated! Detecting...", (10, 30),
# 					cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
# 		cv2.putText(frame, f"Area Range: {int(min_hull_area)} - {int(max_hull_area)}", (10, 60),
# 					cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

# 	roi, thresh, contours = imageFiltering(frame, lower_skin, upper_skin) #getting the filtered image

# 	#blank image which will be used to show the contours and defects
# 	drawing = np.zeros(roi.shape,np.uint8)
	
# 	# === FINGER DETECTION WITH AREA FILTER ===
# 	try:
# 		# Find contour with max area
# 		contour = max(contours, key=lambda x: cv2.contourArea(x), default=0)
		
# 		# Convex hull
# 		hull = cv2.convexHull(contour)
		
# 		# Calculate hull area
# 		current_hull_area = cv2.contourArea(hull)
		
# 		# === AREA FILTER: Only process if within min/max range ===
# 		if area_calibrated and (current_hull_area < min_hull_area or current_hull_area > max_hull_area):
# 			# Out of range - skip detection, just show it's noise
# 			cv2.putText(drawing, "NOISE - Out of range", (10, 30), 
# 					   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
# 			cv2.putText(frame, f"Area: {int(current_hull_area)} (NOISE)", (10, 150),
# 					   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
# 		else:
# 			# Within range or not calibrated yet - proceed with detection
# 			# Draw contours
# 			cv2.drawContours(drawing, [contour], -1, (0, 255, 0), 0)
# 			cv2.drawContours(drawing, [hull], -1, (0, 0, 255), 0)
			
# 			# Display current area
# 			cv2.putText(drawing, f"Area: {int(current_hull_area)}", (10, 30),
# 					   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
			
# 			# Finding defects in the convex polygon
# 			hull = cv2.convexHull(contour, returnPoints=False)
# 			defects = cv2.convexityDefects(contour, hull)
			
# 			count_defects = 0
			
# 			if defects is not None:
# 				for i in range(defects.shape[0]):
# 					s, e, f, d = defects[i, 0]
# 					start = tuple(contour[s][0])
# 					end = tuple(contour[e][0])
# 					far = tuple(contour[f][0])
					
# 					# Calculate angle
# 					a = math.sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2)
# 					b = math.sqrt((far[0] - start[0]) ** 2 + (far[1] - start[1]) ** 2)
# 					c = math.sqrt((end[0] - far[0]) ** 2 + (end[1] - far[1]) ** 2)
# 					angle = (math.acos((b ** 2 + c ** 2 - a ** 2) / (2 * b * c)) * 180) / 3.14
					
# 					# Filter by angle (between fingers should be < 90 degrees)
# 					if angle <= 90:
# 						count_defects += 1
# 						cv2.circle(drawing, far, 5, [0, 0, 255], -1)
					
# 					cv2.line(drawing, start, end, [0, 255, 0], 2)
			
# 			# Display finger count
# 			if count_defects == 0:
# 				cv2.putText(frame, "ONE", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2)
# 			elif count_defects == 1:
# 				cv2.putText(frame, "TWO", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2)
# 			elif count_defects == 2:
# 				cv2.putText(frame, "THREE", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2)
# 			elif count_defects == 3:
# 				cv2.putText(frame, "FOUR", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2)
# 			elif count_defects == 4:
# 				cv2.putText(frame, "FIVE", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2)
	
# 	except Exception as e:
# 		pass
	
# 	# === DRAW TRACKING VISUALIZATION AFTER FINGER DETECTION ===
# 	if calibrated and hand_center is not None:
# 		# Draw tracking ROI (blue box)
# 		cv2.rectangle(frame, (track_x, track_y), 
# 					 (track_x + track_roi_size, track_y + track_roi_size), 
# 					 (255, 0, 0), 2)
		
# 		# Draw hand center
# 		cv2.circle(frame, hand_center, 8, (255, 0, 0), -1)
		
# 		# Draw line between ROI centers
# 		finger_roi_center_x = x + w // 2
# 		finger_roi_center_y = y + h // 2
# 		tracking_roi_center_x = track_x + track_roi_size // 2
# 		tracking_roi_center_y = track_y + track_roi_size // 2
		
# 		cv2.line(frame, (finger_roi_center_x, finger_roi_center_y),
# 				(tracking_roi_center_x, tracking_roi_center_y), (0, 255, 255), 2)
		
# 		# Display distance info
# 		cv2.putText(frame, f"Error X: {int(distance_x)}", (10, frame.shape[0] - 70),
# 				   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
# 		cv2.putText(frame, f"Error Y: {int(distance_y)}", (10, frame.shape[0] - 40),
# 				   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
# 		cv2.putText(frame, f"Distance: {int(distance_total)}", (10, frame.shape[0] - 10),
# 				   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
	
# 	#displaying result
# 	cv2.imshow("thresh",thresh)
# 	cv2.imshow("drawing",drawing)
# 	cv2.imshow("img",frame)
	
# 	# Show hand tracking mask if calibrated
# 	if calibrated and hand_center is not None:
# 		cv2.imshow("Hand Tracking Mask", hand_mask)

# 	k = cv2.waitKey(30) & 0xff #exit if Esc is pressed
	
# 	# Nhấn 'C' để calibrate màu da
# 	if k == ord('c') or k == ord('C'):
# 		if not calibrated:
# 			lower_skin, upper_skin = calibrate_skin_color(frame, sample_boxes)
# 			calibrated = True
# 			print("Skin color calibration complete!")
# 			print(f"Lower HSV: {lower_skin}")
# 			print(f"Upper HSV: {upper_skin}")
	
# 	# Nhấn 'I' để calibrate min hull area (fist)
# 	if k == ord('i') or k == ord('I'):
# 		if calibrated:
# 			min_hull_area = calibrate_hull_area(thresh)
# 			if min_hull_area > 0:
# 				print(f"Min hull area calibrated (FIST): {int(min_hull_area)}")
# 			else:
# 				print("Error: No hand detected in ROI")
	
# 	# Nhấn 'A' để calibrate max hull area (open hand)
# 	if k == ord('a') or k == ord('A'):
# 		if calibrated:
# 			max_hull_area = calibrate_hull_area(thresh)
# 			if max_hull_area > 0:
# 				print(f"Max hull area calibrated (OPEN HAND): {int(max_hull_area)}")
# 				# Check if both min and max are set
# 				if min_hull_area > 0:
# 					area_calibrated = True
# 					print("Area calibration complete! Detection with noise filtering enabled.")
# 			else:
# 				print("Error: No hand detected in ROI")
	
# 	if k == 27:
# 		break

# cap.release() #release the webcam
# cv2.destroyAllWindows() #destroy the window




import cv2
import numpy as np
import math


hand_hist = None
traverse_point = []
total_rectangle = 9
hand_rect_one_x = None
hand_rect_one_y = None

hand_rect_two_x = None
hand_rect_two_y = None


def rescale_frame(frame, wpercent=60, hpercent=60):
    width = int(frame.shape[1] * wpercent / 100)
    height = int(frame.shape[0] * hpercent / 100)
    return cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)

def crop_center(frame):
    
    # Cắt bên trái (1/2 khung hình)
    cropped = frame[100:500, 0:300]
    return cropped
 
def draw_rect(frame):
    rows, cols, _ = frame.shape
    global total_rectangle, hand_rect_one_x, hand_rect_one_y, hand_rect_two_x, hand_rect_two_y

    hand_rect_one_x = np.array(
        [6 * rows / 20, 6 * rows / 20, 6 * rows / 20, 9 * rows / 20, 9 * rows / 20, 9 * rows / 20, 12 * rows / 20,
         12 * rows / 20, 12 * rows / 20], dtype=np.uint32)

    hand_rect_one_y = np.array(
        [9 * cols / 20, 10 * cols / 20, 11 * cols / 20, 9 * cols / 20, 10 * cols / 20, 11 * cols / 20, 9 * cols / 20,
         10 * cols / 20, 11 * cols / 20], dtype=np.uint32)

    hand_rect_two_x = hand_rect_one_x + 10
    hand_rect_two_y = hand_rect_one_y + 10

    for i in range(total_rectangle):
        cv2.rectangle(frame, (hand_rect_one_y[i], hand_rect_one_x[i]),
                      (hand_rect_two_y[i], hand_rect_two_x[i]),
                      (0, 255, 0), 1)

    return frame


def draw_rect_V2(frame):
    """Draw larger rectangles suitable for cropped frame (300x600)"""
    rows, cols, _ = frame.shape
    global total_rectangle, hand_rect_one_x, hand_rect_one_y, hand_rect_two_x, hand_rect_two_y

    # Larger rectangles (30x30 instead of 10x10)
    rect_size = 30
    
    hand_rect_one_x = np.array(
        [6 * rows / 20, 6 * rows / 20, 6 * rows / 20, 9 * rows / 20, 9 * rows / 20, 9 * rows / 20, 12 * rows / 20,
         12 * rows / 20, 12 * rows / 20], dtype=np.uint32)

    hand_rect_one_y = np.array(
        [9 * cols / 20, 10 * cols / 20, 11 * cols / 20, 9 * cols / 20, 10 * cols / 20, 11 * cols / 20, 9 * cols / 20,
         10 * cols / 20, 11 * cols / 20], dtype=np.uint32)

    hand_rect_two_x = hand_rect_one_x + rect_size
    hand_rect_two_y = hand_rect_one_y + rect_size

    for i in range(total_rectangle):
        cv2.rectangle(frame, (hand_rect_one_y[i], hand_rect_one_x[i]),
                      (hand_rect_two_y[i], hand_rect_two_x[i]),
                      (0, 255, 0), 1)  

    return frame



def hand_histogram(frame):
    """Calculate HSV range from 9 green box samples (like commented code)"""
    global hand_rect_one_x, hand_rect_one_y

    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    rect_size = 30
    
    h_values = []
    s_values = []
    v_values = []
    
    # Sample from 9 boxes
    for i in range(total_rectangle):
        roi_sample = hsv_frame[hand_rect_one_x[i]:hand_rect_one_x[i] + rect_size,
                               hand_rect_one_y[i]:hand_rect_one_y[i] + rect_size]
        
        # Collect H, S, V values
        h_values.extend(roi_sample[:, :, 0].flatten())
        s_values.extend(roi_sample[:, :, 1].flatten())
        v_values.extend(roi_sample[:, :, 2].flatten())
    
    # Calculate mean
    h_mean = np.mean(h_values)
    s_mean = np.mean(s_values)
    v_mean = np.mean(v_values)
    
    # More conservative offset values for better accuracy
    h_offset_low = 15
    h_offset_high = 15
    s_offset_low = 50
    s_offset_high = 80
    v_offset_low = 60
    v_offset_high = 80
    
    # Create HSV range with individual offsets per channel
    lower_skin = np.array([
        max(h_mean - h_offset_low, 0),
        max(s_mean - s_offset_low, 0),
        max(v_mean - v_offset_low, 0)
    ], dtype=np.uint8)
    
    upper_skin = np.array([
        min(h_mean + h_offset_high, 179),
        min(s_mean + s_offset_high, 255),
        min(v_mean + v_offset_high, 255)
    ], dtype=np.uint8)
    
    print(f"Skin calibration - H: {h_mean:.1f}, S: {s_mean:.1f}, V: {v_mean:.1f}")
    print(f"Lower HSV: {lower_skin}")
    print(f"Upper HSV: {upper_skin}")
    
    return lower_skin, upper_skin

def hist_masking(frame, skin_range):
    """Apply HSV range mask (like commented code imageFiltering)"""
    lower_skin, upper_skin = skin_range
    
    # Apply Gaussian blur to reduce noise
    blur = cv2.GaussianBlur(frame, (5, 5), 0)
    
    # Convert to HSV
    hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)
    
    # Apply skin color mask
    mask = cv2.inRange(hsv, lower_skin, upper_skin)
    
    # Reduce noise
    filtered = cv2.GaussianBlur(mask, (3, 3), 0)
    ret, thresh = cv2.threshold(filtered, 127, 255, 0)
    thresh = cv2.GaussianBlur(thresh, (5, 5), 0)
    
    # Merge to 3 channels for display
    thresh_3channel = cv2.merge((thresh, thresh, thresh))
    
    return cv2.bitwise_and(frame, thresh_3channel)


def centroid(max_contour):
    moment = cv2.moments(max_contour)
    if moment['m00'] != 0:
        cx = int(moment['m10'] / moment['m00'])
        cy = int(moment['m01'] / moment['m00'])
        return cx, cy
    else:
        return None
    


def contours(hist_mask_image):
    gray_hist_mask_image = cv2.cvtColor(hist_mask_image, cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(gray_hist_mask_image, 0, 255, 0)
    cont, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    return cont

def manage_image_opr(frame, hand_hist):
    hist_mask_image = hist_masking(frame, hand_hist)

    hist_mask_image = cv2.erode(hist_mask_image, None, iterations=2)
    hist_mask_image = cv2.dilate(hist_mask_image, None, iterations=2)

    contour_list = contours(hist_mask_image)
    
    cnt_centroid = None
    is_hand = False
    validation_msg = "NO HAND"
    
    if len(contour_list) > 0:
        max_cont = max(contour_list, key=cv2.contourArea)
        
        # Validate if it's actually a hand
        is_hand, validation_msg = validate_hand_contour(max_cont, frame)
        
        if is_hand:
            cnt_centroid = centroid(max_cont)
            if cnt_centroid is not None:
                cv2.circle(frame, cnt_centroid, 5, [255, 0, 255], -1)
                # Display "HAND DETECTED" on frame
                cv2.putText(frame, "HAND DETECTED", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            # Not a hand - display warning
            cv2.putText(frame, validation_msg, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    return cnt_centroid, is_hand


def validate_hand_contour(contour, frame):
    """Validate if contour is actually a hand based on shape and position"""
    frame_height, frame_width = frame.shape[:2]
    
    # Get bounding box
    x, y, w, h = cv2.boundingRect(contour)
    
    # Calculate area
    area = cv2.contourArea(contour)
    
    # Calculate aspect ratio (height / width)
    aspect_ratio = h / w if w > 0 else 0
    
    # Validation checks
    # 1. Minimum area (filter out noise)
    if area < 1000:
        return False, "NO HAND: Too small"
    
    # 2. Maximum area (filter out full-frame detection)
    if area > (frame_width * frame_height * 0.8):
        return False, "NO HAND: Too large"
    
    # 3. Aspect ratio - hand should be somewhat vertical (relaxed constraint)
    if aspect_ratio < 0.5:
        return False, "NO HAND: Wrong shape"
    
    # 4. Position check - more relaxed (allow closer to edges)
    if x < 5 or x + w > frame_width - 5:
        return False, "NO HAND: Edge position"
    
    # 5. Centroid should be in reasonable vertical area (relaxed)
    M = cv2.moments(contour)
    if M["m00"] != 0:
        cy = int(M["m01"] / M["m00"])
        if cy < frame_height * 0.1:
            return False, "NO HAND: Too high"
    
    # All checks passed
    return True, "HAND DETECTED"

# def imageFiltering(frame, lower_skin, upper_skin):

# 	#area of intereset(hand)
# 	roi = frame[y:y+h,x:x+w]

# 	#applying gaussian blurr to reduce the noise
# 	blur = cv2.GaussianBlur(roi,(5,5),0)
# 	#converting from coloured to HSV
# 	hsv = cv2.cvtColor(blur,cv2.COLOR_BGR2HSV)

# 	#applying a mask which makes skin color white and others black
# 	mask = cv2.inRange(hsv, lower_skin, upper_skin)

# 	kernel = np.ones((5,5))
# 	#reducing noise
# 	filtered = cv2.GaussianBlur(mask,(3,3),0)
# 	ret,thresh = cv2.threshold(filtered,127,255,0) #thesholding the image
# 	thesh = cv2.GaussianBlur(thresh,(5,5),0) #reducing the noise
# 	#finding contours in the image. Will be used later in complex hull algorithm
# 	contours,hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

# 	return roi, thresh, contours

def main():
    global hand_hist
    is_hand_hist_created = False
    capture = cv2.VideoCapture(0)

    while capture.isOpened():
        pressed_key = cv2.waitKey(1)
        _, frame = capture.read()
        height, width = frame.shape[:2]
        frame = cv2.flip(frame, 1)
        frame_copy = frame.copy()
        frame_copy = crop_center(frame_copy)

        if pressed_key & 0xFF == ord('z'):
            is_hand_hist_created = True
            hand_hist = hand_histogram(frame_copy)

        hand_centroid_cropped = None
        distance_x = 0
        distance_y = 0
        distance_total = 0
        
        # Get center of cropped frame
        cropped_height, cropped_width = frame_copy.shape[:2]
        center_x = cropped_width // 2
        center_y = cropped_height // 2
        
        # Draw red point in the middle of cropped frame
        cv2.circle(frame_copy, (center_x, center_y), 8, [0, 0, 255], -1)
        cv2.putText(frame_copy, "TARGET", (center_x - 30, center_y - 15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        if is_hand_hist_created:
            # Create clean frame for mask (without text overlays)
            frame_copy_clean = crop_center(frame.copy())
            
            hand_centroid_cropped, is_hand = manage_image_opr(frame_copy, hand_hist)
            
            # Calculate distance if hand is detected
            if hand_centroid_cropped is not None and is_hand:
                # Distance from hand centroid to center (red point)
                distance_x = hand_centroid_cropped[0] - center_x
                distance_y = hand_centroid_cropped[1] - center_y
                distance_total = int(np.sqrt(distance_x**2 + distance_y**2))
                
                # Draw line connecting purple point to red center
                cv2.line(frame_copy, hand_centroid_cropped, (center_x, center_y), 
                        (255, 255, 0), 2)
                
                # Display distance info on cropped frame
                cv2.putText(frame_copy, f"Error X: {int(distance_x)}", (10, cropped_height - 70),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
                cv2.putText(frame_copy, f"Error Y: {int(distance_y)}", (10, cropped_height - 45),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
                cv2.putText(frame_copy, f"Distance: {distance_total}", (10, cropped_height - 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
                
                # Draw purple point on Live Feed frame (convert cropped coordinates to full frame)
                # Cropped frame is [100:500, 0:300]
                # So x stays same, but y needs +100 offset
                cx_full = hand_centroid_cropped[0]  # X stays same (starts at 0)
                cy_full = hand_centroid_cropped[1] + 100  # Y needs +100 offset
                cv2.circle(frame, (cx_full, cy_full), 8, [255, 0, 255], -1)
                
                # Also draw red center point on Live Feed
                center_x_full = center_x
                center_y_full = center_y + 100
                cv2.circle(frame, (center_x_full, center_y_full), 8, [0, 0, 255], -1)

        else:
            frame_copy = draw_rect_V2(frame_copy)  # Use V2 for cropped frame

        # cv2.imshow("Live Feed", rescale_frame(frame))
        cv2.imshow("Live Feed", frame)
        cv2.imshow("Cropped", frame_copy)
        
        if is_hand_hist_created:
            cv2.imshow("Hist mask image", hist_masking(frame_copy_clean, hand_hist))
            
        
        if pressed_key == 27:
            break

    cv2.destroyAllWindows()
    capture.release()

if __name__ == '__main__':
    main()