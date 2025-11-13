import cv2
import numpy as np
import math


def draw_skin_sample_boxes(frame):
	"""Vẽ 3 ô vuông dọc để lấy mẫu màu da"""
	frame_height, frame_width = frame.shape[:2]
	
	# Vị trí các ô vuông (bên phải màn hình, dọc theo chiều cao)
	box_size = 20  # Kích thước mỗi ô
	x_pos = frame_width // 5  # Vị trí X (1/5 từ trái)
	
	# 3 ô vuông dọc: trên, giữa, dưới
	boxes = [
		(x_pos, frame_height // 3, box_size, box_size),      # Ô trên
		(x_pos, frame_height // 2, box_size, box_size),      # Ô giữa  
		(x_pos, 2 * frame_height // 3, box_size, box_size)   # Ô dưới
	]
	
	# Vẽ các ô vuông màu tím (để dễ nhìn)
	for (x, y, w, h) in boxes:
		cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 255), 2)
	
	return boxes


def calibrate_skin_color(frame, boxes):
	"""Lấy mẫu màu da từ 3 ô vuông và tính ngưỡng HSV"""
	hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
	
	h_values = []
	s_values = []
	v_values = []
	
	# Lấy mẫu từ 3 ô vuông
	for (x, y, w, h) in boxes:
		roi_sample = hsv_frame[y:y+h, x:x+w]
		
		# Thu thập giá trị H, S, V
		h_values.extend(roi_sample[:, :, 0].flatten())
		s_values.extend(roi_sample[:, :, 1].flatten())
		v_values.extend(roi_sample[:, :, 2].flatten())
	
	# Tính mean của tất cả samples
	h_mean = np.mean(h_values)
	s_mean = np.mean(s_values)
	v_mean = np.mean(v_values)
	
	# Tính offset như trong Handy C++ (±80 cho low, ±30 cho high)
	offset_low = 80
	offset_high = 30
	
	# Tạo ngưỡng HSV
	lower_skin = np.array([
		max(h_mean - offset_low, 0),
		max(s_mean - offset_low, 0),
		max(v_mean - offset_low, 0)
	], dtype=np.uint8)
	
	upper_skin = np.array([
		min(h_mean + offset_high, 179),
		min(s_mean + offset_high, 255),
		min(v_mean + offset_high, 255)
	], dtype=np.uint8)
	
	return lower_skin, upper_skin


def calibrate_hull_area(thresh):
	"""Tính hull area từ thresh để calibrate min/max area"""
	try:
		# Find contours on thresh
		contours_roi, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
		
		if len(contours_roi) > 0:
			# Get largest contour
			contour = max(contours_roi, key=cv2.contourArea)
			
			# Get convex hull
			hull = cv2.convexHull(contour)
			
			# Calculate hull area
			hull_area = cv2.contourArea(hull)
			
			return hull_area
	except:
		pass
	
	return 0


def imageFiltering(frame, lower_skin, upper_skin):

	#area of intereset(hand)
	roi = frame[y:y+h,x:x+w]

	#applying gaussian blurr to reduce the noise
	blur = cv2.GaussianBlur(roi,(5,5),0)
	#converting from coloured to HSV
	hsv = cv2.cvtColor(blur,cv2.COLOR_BGR2HSV)

	#applying a mask which makes skin color white and others black
	mask = cv2.inRange(hsv, lower_skin, upper_skin)

	kernel = np.ones((5,5))
	#reducing noise
	filtered = cv2.GaussianBlur(mask,(3,3),0)
	ret,thresh = cv2.threshold(filtered,127,255,0) #thesholding the image
	thesh = cv2.GaussianBlur(thresh,(5,5),0) #reducing the noise
	#finding contours in the image. Will be used later in complex hull algorithm
	contours,hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

	return roi, thresh, contours


cap = cv2.VideoCapture(0)

#dimensions of the box
x = 100
y = 100
w = 200
h = 200

# Biến cho skin calibration
calibrated = False
lower_skin = np.array([2, 50, 50])
upper_skin = np.array([20, 255, 255])

# Biến cho hull area calibration
min_hull_area = 0
max_hull_area = float('inf')
area_calibrated = False

while True:
	ret,frame = cap.read() #read video frame by frame
	
	if not ret:
		print("Cannot read frame")
		break
	
	frame = cv2.flip(frame, 1)  # Flip horizontal
	
	#create a rectangle around roi
	cv2.rectangle(frame,(x, y), (x+w, y+h), (0,255,0), 2)
	
	# Chỉ vẽ 3 ô vuông để lấy mẫu màu da khi chưa calibrate
	if not calibrated:
		sample_boxes = draw_skin_sample_boxes(frame)
		# Hiển thị hướng dẫn
		cv2.putText(frame, "Place hand in purple boxes", (10, 30),
					cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
		cv2.putText(frame, "Press 'C' to calibrate skin", (10, 60),
					cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
	elif not area_calibrated:
		cv2.putText(frame, "Make FIST in green box, press 'I' for min area", (10, 30),
					cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
		cv2.putText(frame, "Open 5 FINGERS, press 'A' for max area", (10, 60),
					cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
		if min_hull_area > 0:
			cv2.putText(frame, f"Min Area: {int(min_hull_area)}", (10, 90),
						cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
		if max_hull_area < float('inf'):
			cv2.putText(frame, f"Max Area: {int(max_hull_area)}", (10, 120),
						cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
	else:
		cv2.putText(frame, "Calibrated! Detecting...", (10, 30),
					cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
		cv2.putText(frame, f"Area Range: {int(min_hull_area)} - {int(max_hull_area)}", (10, 60),
					cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

	roi, thresh, contours = imageFiltering(frame, lower_skin, upper_skin) #getting the filtered image

	#blank image which will be used to show the contours and defects
	drawing = np.zeros(roi.shape,np.uint8)
	
	# === FINGER DETECTION WITH AREA FILTER ===
	try:
		# Find contour with max area
		contour = max(contours, key=lambda x: cv2.contourArea(x), default=0)
		
		# Convex hull
		hull = cv2.convexHull(contour)
		
		# Calculate hull area
		current_hull_area = cv2.contourArea(hull)
		
		# === AREA FILTER: Only process if within min/max range ===
		if area_calibrated and (current_hull_area < min_hull_area or current_hull_area > max_hull_area):
			# Out of range - skip detection, just show it's noise
			cv2.putText(drawing, "NOISE - Out of range", (10, 30), 
					   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
			cv2.putText(frame, f"Area: {int(current_hull_area)} (NOISE)", (10, 150),
					   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
		else:
			# Within range or not calibrated yet - proceed with detection
			# Draw contours
			cv2.drawContours(drawing, [contour], -1, (0, 255, 0), 0)
			cv2.drawContours(drawing, [hull], -1, (0, 0, 255), 0)
			
			# Display current area
			cv2.putText(drawing, f"Area: {int(current_hull_area)}", (10, 30),
					   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
			
			# Finding defects in the convex polygon
			hull = cv2.convexHull(contour, returnPoints=False)
			defects = cv2.convexityDefects(contour, hull)
			
			count_defects = 0
			
			if defects is not None:
				for i in range(defects.shape[0]):
					s, e, f, d = defects[i, 0]
					start = tuple(contour[s][0])
					end = tuple(contour[e][0])
					far = tuple(contour[f][0])
					
					# Calculate angle
					a = math.sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2)
					b = math.sqrt((far[0] - start[0]) ** 2 + (far[1] - start[1]) ** 2)
					c = math.sqrt((end[0] - far[0]) ** 2 + (end[1] - far[1]) ** 2)
					angle = (math.acos((b ** 2 + c ** 2 - a ** 2) / (2 * b * c)) * 180) / 3.14
					
					# Filter by angle (between fingers should be < 90 degrees)
					if angle <= 90:
						count_defects += 1
						cv2.circle(drawing, far, 5, [0, 0, 255], -1)
					
					cv2.line(drawing, start, end, [0, 255, 0], 2)
			
			# Display finger count
			if count_defects == 0:
				cv2.putText(frame, "ONE", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2)
			elif count_defects == 1:
				cv2.putText(frame, "TWO", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2)
			elif count_defects == 2:
				cv2.putText(frame, "THREE", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2)
			elif count_defects == 3:
				cv2.putText(frame, "FOUR", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2)
			elif count_defects == 4:
				cv2.putText(frame, "FIVE", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2)
	
	except Exception as e:
		pass
	
	#displaying result
	cv2.imshow("thresh",thresh)
	cv2.imshow("drawing",drawing)
	cv2.imshow("img",frame)

	k = cv2.waitKey(30) & 0xff #exit if Esc is pressed
	
	# Nhấn 'C' để calibrate màu da
	if k == ord('c') or k == ord('C'):
		if not calibrated:
			lower_skin, upper_skin = calibrate_skin_color(frame, sample_boxes)
			calibrated = True
			print("Skin color calibration complete!")
			print(f"Lower HSV: {lower_skin}")
			print(f"Upper HSV: {upper_skin}")
	
	# Nhấn 'I' để calibrate min hull area (fist)
	if k == ord('i') or k == ord('I'):
		if calibrated:
			min_hull_area = calibrate_hull_area(thresh)
			if min_hull_area > 0:
				print(f"Min hull area calibrated (FIST): {int(min_hull_area)}")
			else:
				print("Error: No hand detected in ROI")
	
	# Nhấn 'A' để calibrate max hull area (open hand)
	if k == ord('a') or k == ord('A'):
		if calibrated:
			max_hull_area = calibrate_hull_area(thresh)
			if max_hull_area > 0:
				print(f"Max hull area calibrated (OPEN HAND): {int(max_hull_area)}")
				# Check if both min and max are set
				if min_hull_area > 0:
					area_calibrated = True
					print("Area calibration complete! Detection with noise filtering enabled.")
			else:
				print("Error: No hand detected in ROI")
	
	if k == 27:
		break

cap.release() #release the webcam
cv2.destroyAllWindows() #destroy the window