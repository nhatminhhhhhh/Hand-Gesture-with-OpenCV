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

# Global skin color range
lower_skin = None
upper_skin = None


def rescale_frame(frame, wpercent=130, hpercent=130):
    width = int(frame.shape[1] * wpercent / 100)
    height = int(frame.shape[0] * hpercent / 100)
    return cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)

def crop_center(frame):
    
    # Cắt bên trái (1/2 khung hình)
    cropped = frame[100:500, 0:400]
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



def hand_hsv_func(frame):
    """Calculate HSV range from 9 green box samples (like commented code)"""
    global hand_rect_one_x, hand_rect_one_y, lower_skin, upper_skin

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

def manage_image_opr(frame, hand_hsv):
    hist_mask_image = hist_masking(frame, hand_hsv)

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
    if x < 5 or x + w > frame_width - 2:
        return False, "NO HAND: Edge position"
    
    # 5. Centroid should be in reasonable vertical area (relaxed)
    M = cv2.moments(contour)
    if M["m00"] != 0:
        cy = int(M["m01"] / M["m00"])
        if cy < frame_height * 0.1:
            return False, "NO HAND: Too high"
    
    # All checks passed
    return True, "HAND DETECTED"

def imageFiltering(frame, lower_skin, upper_skin):

    # area of interest (hand)
    roi = frame.copy()

    # applying gaussian blur to reduce the noise
    blur = cv2.GaussianBlur(roi, (5, 5), 0)
    # converting from coloured to HSV
    hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)

    # applying a mask which makes skin color white and others black
    mask = cv2.inRange(hsv, lower_skin, upper_skin)

    kernel = np.ones((5, 5), np.uint8)
    # reducing noise
    filtered = cv2.GaussianBlur(mask, (3, 3), 0)
    ret, thresh = cv2.threshold(filtered, 127, 255, 0)  # thresholding the image
    thresh = cv2.GaussianBlur(thresh, (5,5), 0) # reducing the noise
    kernel2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (4, 4))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel2, iterations=2)
    # finding contours in the image. Will be used later in complex hull algorithm
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    return roi, thresh, contours


def main():
    global hand_hsv, lower_skin, upper_skin
    is_hand_created = False
    capture = cv2.VideoCapture(0)

    while capture.isOpened():
        pressed_key = cv2.waitKey(1)
        _, frame = capture.read()
        # height, width = frame.shape[:2]
        frame = cv2.flip(frame, 1)
        frame_copy = frame.copy()
        frame_copy = crop_center(frame_copy)

        if pressed_key & 0xFF == ord('z'):
            is_hand_created = True
            hand_hsv = hand_hsv_func(frame_copy)
        
        if pressed_key & 0xFF == ord('r'):
            is_hand_created = False
            hand_hsv = None
            lower_skin = None
            upper_skin = None
            print("Recalibration mode - Press 'z' to calibrate skin color")

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
        
        if is_hand_created:
            # Create clean frame for mask (without text overlays)
            frame_copy_clean = crop_center(frame.copy())
            
            hand_centroid_cropped, is_hand = manage_image_opr(frame_copy, hand_hsv)
            
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
                # cv2.imshow("Hist mask image",hist_masking(frame_copy_clean, hand_hsv_func))
                roi, thresh, contours = imageFiltering(frame_copy_clean, lower_skin, upper_skin) #getting the filtered image

                #blank image which will be used to show the contours and defects
                drawing = np.zeros(roi.shape,np.uint8)
                
                # Draw white centroid point on drawing window if hand detected
                if hand_centroid_cropped is not None and is_hand:
                    cv2.circle(drawing, hand_centroid_cropped, 5, [255, 255, 255], -1)
                        # === FINGER DETECTION WITH AREA FILTER ===
                    try:
                        # Find contour with max area
                        contour = max(contours, key=lambda x: cv2.contourArea(x), default=0)
                        
                        # Convex hull
                        hull = cv2.convexHull(contour)
                        
                        # Calculate hull area
                        current_hull_area = cv2.contourArea(hull)
                        # Calculate area ratio
                        contour_area = cv2.contourArea(contour)
                        area_ratio = (contour_area / current_hull_area * 100) if current_hull_area > 0 else 0
                        
                        # Find the highest point (minimum Y value) of the contour
                        highest_point = tuple(contour[contour[:, :, 1].argmin()][0])
                        
                        # Calculate distance from highest point to centroid (white point)
                        highest_point_distance = 0
                        # if hand_centroid_cropped is not None:
                        highest_point_distance = math.sqrt(
                            (highest_point[0] - hand_centroid_cropped[0]) ** 2 + 
                            (highest_point[1] - hand_centroid_cropped[1]) ** 2
                        )
                            # Draw the highest point for visualization
                        cv2.circle(drawing, highest_point, 5, [0, 255, 255], -1)  # Yellow dot
                            # cv2.line(drawing, hand_centroid_cropped, highest_point, [255, 255, 0], 1)  # Cyan line
                        
                        # Within range or not calibrated yet - proceed with detection
                        # Draw contours
                        cv2.drawContours(drawing, [contour], -1, (0, 255, 0), 0)
                        # cv2.drawContours(drawing, [hull], -1, (255, 255, 255), 0)
                        
                        # Display current area
                        cv2.putText(drawing, f"Area: {int(current_hull_area)}", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
                        cv2.putText(drawing, f"Ratio: {area_ratio:.1f}%", (10, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
                        cv2.putText(drawing, f"HighDist: {int(highest_point_distance)}", (10, 70),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
                        
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
                                
                                # Calculate distance from centroid to start and end points
                                dist_to_start = math.sqrt((hand_centroid_cropped[0] - start[0]) ** 2 + 
                                                        (hand_centroid_cropped[1] - start[1]) ** 2)
                                dist_to_end = math.sqrt((hand_centroid_cropped[0] - end[0]) ** 2 + 
                                                    (hand_centroid_cropped[1] - end[1]) ** 2)
                                
                                # Calculate Y difference (negative means fingertip is ABOVE centroid)
                                y_diff_start = start[1] - hand_centroid_cropped[1]
                                y_diff_end = end[1] - hand_centroid_cropped[1]
                                
                                # Valid finger detection criteria
                                min_fingertip_distance = 70
                                    
                                if (angle >= 25 and angle <= 80 and d > 10000 and 
                                    dist_to_start > min_fingertip_distance and dist_to_end > min_fingertip_distance and
                                    y_diff_start < 0 and y_diff_end < 0):
                                    count_defects += 1
                                    # Draw defect visualization
                                    cv2.circle(drawing, far, 5, [0, 0, 255], -1)  # Red circle at valley point
                                    cv2.line(drawing, hand_centroid_cropped, start, [0, 255, 255], 1)  # Cyan line to start
                                    cv2.line(drawing, hand_centroid_cropped, end, [0, 255, 255], 1)  # Cyan line to end
                                
                                cv2.line(drawing, start, end, [0, 100, 0], 2)
                        
                        # Distinguish FIST from real fingers using highest point distance
                        # This helps avoid false positives from shadows/gaps in FIST
                        min_one_finger_distance = 150
                        
                        if count_defects == 0:
                            # No defects detected
                            if highest_point_distance > min_one_finger_distance:
                                # Highest point far from centroid = ONE finger extended
                                cv2.line(drawing, hand_centroid_cropped, highest_point, [255, 255, 0], 1)
                                print("One finger detected - Distance:", highest_point_distance)
                            else:
                                # Highest point close to centroid = FIST
                                print("FIST detected - Distance:", highest_point_distance)
                        
                        elif count_defects >= 1:
                            # Defects detected - check if it's real fingers or just shadow noise
                            if highest_point_distance < min_one_finger_distance:
                                # Highest point is close to centroid = FIST with shadow artifacts
                                # Ignore the defects - it's actually a FIST
                                print(f"FIST detected (shadow defects ignored) - HighDist: {highest_point_distance}, Defects: {count_defects}")
                            else:
                                # Highest point is far = real extended fingers
                                if count_defects == 1:
                                    print("Two fingers detected")
                                elif count_defects == 2:
                                    print("Three fingers detected")
                                elif count_defects == 3:
                                    print("Four fingers detected")
                                elif count_defects == 4:
                                    print("Five fingers detected")
                            
                    except Exception as e:
                        pass
                cv2.imshow("thresh",thresh)
                cv2.imshow("drawing",drawing)

        else:
            frame_copy = rescale_frame(draw_rect_V2(frame_copy))  # Use V2 for cropped frame
            # Show instruction
            cv2.putText(frame_copy, "Press 'z' to calibrate skin color", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # cv2.imshow("Live Feed", rescale_frame(frame))
        # cv2.imshow("Live Feed", frame)
        cv2.imshow("Cropped", frame_copy)
        
        if pressed_key == 27:
            break

    cv2.destroyAllWindows()
    capture.release()

if __name__ == '__main__':
    main()