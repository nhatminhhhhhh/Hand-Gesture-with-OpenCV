import cv2
import numpy as np
import math
import serial
import time

# ============================================================================
# CONFIGURATION
# ============================================================================
CONFIG = {
    # Frame cropping (Y_start, Y_end, X_start, X_end)
    'CROP_REGION': (100, 500, 0, 400),
    
    # Skin color calibration
    'CALIBRATION_BOXES': 9,
    'BOX_SIZE': 30,
    'HSV_OFFSETS': {
        'H_LOW': 15, 'H_HIGH': 15,
        'S_LOW': 50, 'S_HIGH': 80,
        'V_LOW': 60, 'V_HIGH': 80
    },
    # YCrCb offsets for calibration
    'YCRCB_OFFSETS': {
        'Y_LOW': 20, 'Y_HIGH': 20,
        'Cr_LOW': 20, 'Cr_HIGH': 20,
        'Cb_LOW': 20, 'Cb_HIGH': 20
    },
    
    # Hand validation thresholds
    'MIN_HAND_AREA': 1000,
    'MAX_HAND_AREA_RATIO': 0.8,  # Fraction of frame
    'MIN_ASPECT_RATIO': 0.5,
    'EDGE_MARGIN': 5,
    'MIN_CENTROID_HEIGHT_RATIO': 0.1,
    
    # Finger detection thresholds
    'ANGLE_RANGE': (25, 80),  # Degrees for valid finger valley
    'DEFECT_DEPTH_THRESHOLD': 10000,  # Minimum depth for valley
    'MIN_FINGERTIP_DIST': 70,  # Min distance from centroid to fingertip
    'MIN_ONE_FINGER_DIST': 120,  # Min distance for ONE finger detection
    
    # Morphological operations
    'MORPH_KERNEL_SIZE': (4, 4),
    'MORPH_ITERATIONS': 2,
    
    # Display settings
    'RESCALE_PERCENT': 130
}

# ============================================================================
# GLOBAL VARIABLES
# ============================================================================
total_rectangle = CONFIG['CALIBRATION_BOXES']
hand_rect_one_x = None
hand_rect_one_y = None
hand_rect_two_x = None
hand_rect_two_y = None

# Global skin color range
lower_skin = None
upper_skin = None

# Calibration state tracking
calibration_stage = 0  # 0: not started, 1: palm calibrated, 2: both calibrated
palm_hsv_range = None  # Store palm HSV range
back_hsv_range = None  # Store back of hand HSV range
# YCrCb ranges
palm_ycrcb_range = None
back_ycrcb_range = None

# Combined YCrCb skin range
lower_skin_ycrcb = None
upper_skin_ycrcb = None

# Anti-flicker filter for finger detection
from collections import deque
finger_count_history = deque(maxlen=5)  # Store last 5 finger counts
FINGER_COUNT_THRESHOLD = 3  # Minimum occurrences to confirm finger count change


def rescale_frame(frame, wpercent=None, hpercent=None):
    """Rescale frame for display"""
    if wpercent is None:
        wpercent = CONFIG['RESCALE_PERCENT']
    if hpercent is None:
        hpercent = CONFIG['RESCALE_PERCENT']
    width = int(frame.shape[1] * wpercent / 100)
    height = int(frame.shape[0] * hpercent / 100)
    return cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)

def crop_center(frame):
    """Crop frame to region of interest"""
    y1, y2, x1, x2 = CONFIG['CROP_REGION']
    cropped = frame[y1:y2, x1:x2]
    return cropped

def draw_rect_V2(frame):
    """Draw calibration rectangles on frame"""
    rows, cols, _ = frame.shape
    global total_rectangle, hand_rect_one_x, hand_rect_one_y, hand_rect_two_x, hand_rect_two_y

    rect_size = CONFIG['BOX_SIZE']
    
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



def hand_hsv_func(frame, calibration_type="palm"):
    """Calculate HSV range from calibration box samples
    
    Args:
        frame: Input frame with calibration boxes
        calibration_type: "palm" or "back" - which side of hand is being calibrated
    
    Returns:
        (lower_hsv, upper_hsv) arrays
    """
    global hand_rect_one_x, hand_rect_one_y

    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    rect_size = CONFIG['BOX_SIZE']
    
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
    
    # Get offset values from config
    h_offset_low = CONFIG['HSV_OFFSETS']['H_LOW']
    h_offset_high = CONFIG['HSV_OFFSETS']['H_HIGH']
    s_offset_low = CONFIG['HSV_OFFSETS']['S_LOW']
    s_offset_high = CONFIG['HSV_OFFSETS']['S_HIGH']
    v_offset_low = CONFIG['HSV_OFFSETS']['V_LOW']
    v_offset_high = CONFIG['HSV_OFFSETS']['V_HIGH']
    
    # Create HSV range with individual offsets per channel
    lower = np.array([
        max(h_mean - h_offset_low, 0),
        max(s_mean - s_offset_low, 0),
        max(v_mean - v_offset_low, 0)
    ], dtype=np.uint8)
    
    upper = np.array([
        min(h_mean + h_offset_high, 179),
        min(s_mean + s_offset_high, 255),
        min(v_mean + v_offset_high, 255)
    ], dtype=np.uint8)
    
    print(f"\n{calibration_type.upper()} calibration:")
    print(f"  H: {h_mean:.1f}, S: {s_mean:.1f}, V: {v_mean:.1f}")
    print(f"  Lower HSV: {lower}")
    print(f"  Upper HSV: {upper}")
    
    return lower, upper


def hand_ycrcb_func(frame, calibration_type="palm"):
    """Calculate YCrCb range from calibration box samples

    Args:
        frame: Input frame with calibration boxes
        calibration_type: "palm" or "back"

    Returns:
        tuple: (lower_ycrcb, upper_ycrcb) arrays
    """
    global hand_rect_one_x, hand_rect_one_y

    ycrcb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
    rect_size = CONFIG['BOX_SIZE']

    y_values = []
    cr_values = []
    cb_values = []

    for i in range(total_rectangle):
        roi_sample = ycrcb_frame[hand_rect_one_x[i]:hand_rect_one_x[i] + rect_size,
                                hand_rect_one_y[i]:hand_rect_one_y[i] + rect_size]
        y_values.extend(roi_sample[:, :, 0].flatten())
        cr_values.extend(roi_sample[:, :, 1].flatten())
        cb_values.extend(roi_sample[:, :, 2].flatten())

    y_mean = np.mean(y_values)
    cr_mean = np.mean(cr_values)
    cb_mean = np.mean(cb_values)

    offs = CONFIG['YCRCB_OFFSETS']
    lower = np.array([
        max(y_mean - offs['Y_LOW'], 0),
        max(cr_mean - offs['Cr_LOW'], 0),
        max(cb_mean - offs['Cb_LOW'], 0)
    ], dtype=np.uint8)

    upper = np.array([
        min(y_mean + offs['Y_HIGH'], 255),
        min(cr_mean + offs['Cr_HIGH'], 255),
        min(cb_mean + offs['Cb_HIGH'], 255)
    ], dtype=np.uint8)

    print(f"\n{calibration_type.upper()} YCrCb calibration:")
    print(f"  Y: {y_mean:.1f}, Cr: {cr_mean:.1f}, Cb: {cb_mean:.1f}")
    print(f"  Lower YCrCb: {lower}")
    print(f"  Upper YCrCb: {upper}")

    return lower, upper


def combine_ycrcb_ranges(palm_range, back_range):
    lower_palm, upper_palm = palm_range
    lower_back, upper_back = back_range
    combined_lower = np.array([
        min(lower_palm[0], lower_back[0]),
        min(lower_palm[1], lower_back[1]),
        min(lower_palm[2], lower_back[2])
    ], dtype=np.uint8)
    combined_upper = np.array([
        max(upper_palm[0], upper_back[0]),
        max(upper_palm[1], upper_back[1]),
        max(upper_palm[2], upper_back[2])
    ], dtype=np.uint8)

    print(f"\nCOMBINED YCrCb range:")
    print(f"  Lower: {combined_lower}")
    print(f"  Upper: {combined_upper}")
    return combined_lower, combined_upper


def combine_hsv_ranges(palm_range, back_range):
    """Combine two HSV ranges to create a unified range that covers both
    
    Args:
        palm_range: tuple of (lower_palm, upper_palm)
        back_range: tuple of (lower_back, upper_back)
    
    Returns:
        tuple: (combined_lower, combined_upper)
    """
    lower_palm, upper_palm = palm_range
    lower_back, upper_back = back_range
    
    # Take minimum of lower bounds and maximum of upper bounds for each channel
    combined_lower = np.array([
        min(lower_palm[0], lower_back[0]),
        min(lower_palm[1], lower_back[1]),
        min(lower_palm[2], lower_back[2])
    ], dtype=np.uint8)
    
    combined_upper = np.array([
        max(upper_palm[0], upper_back[0]),
        max(upper_palm[1], upper_back[1]),
        max(upper_palm[2], upper_back[2])
    ], dtype=np.uint8)
    
    print(f"\nCOMBINED HSV range:")
    print(f"  Lower: {combined_lower}")
    print(f"  Upper: {combined_upper}")
    
    return combined_lower, combined_upper


def get_stable_finger_count(current_count):  
    """
    Args:
        current_count: Current frame's detected finger count
    Returns:
        int: Stabilized finger count
    """
    global finger_count_history
    
    # Add current count to history
    finger_count_history.append(current_count)
    
    # If don't have enough history yet, return current count
    if len(finger_count_history) < 3:
        return current_count
    
    # Use majority voting - return most common count in recent history
    from collections import Counter
    count_freq = Counter(finger_count_history)
    most_common_count, frequency = count_freq.most_common(1)[0]
    
    # Only change to new count if it appears at least THRESHOLD times
    if frequency >= FINGER_COUNT_THRESHOLD:
        return most_common_count
    else:
        # Return the previous stable count (second most recent unique value)
        if len(finger_count_history) >= 2:
            return finger_count_history[-2]
        return current_count

def centroid(max_contour):
    """Calculate centroid of contour using moments"""
    moment = cv2.moments(max_contour)
    if moment['m00'] != 0:
        cx = int(moment['m10'] / moment['m00'])
        cy = int(moment['m01'] / moment['m00'])
        return cx, cy
    else:
        return None

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
    if area < CONFIG['MIN_HAND_AREA']:
        return False, "NO HAND: Too small"
    
    # 2. Maximum area (filter out full-frame detection)
    if area > (frame_width * frame_height * CONFIG['MAX_HAND_AREA_RATIO']):
        return False, "NO HAND: Too large"
    
    # 3. Aspect ratio - hand should be somewhat vertical
    if aspect_ratio < CONFIG['MIN_ASPECT_RATIO']:
        return False, "NO HAND: Wrong shape"
    
    # # 4. Position check (allow some margin from edges)
    # if x < CONFIG['EDGE_MARGIN'] or x + w > frame_width - CONFIG['EDGE_MARGIN']:
    #     return False, "NO HAND: Edge position"
    
    # 5. Centroid should be in reasonable vertical area
    M = cv2.moments(contour)
    if M["m00"] != 0:
        cy = int(M["m01"] / M["m00"])
        if cy < frame_height * CONFIG['MIN_CENTROID_HEIGHT_RATIO']:
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
    mask_hsv = cv2.inRange(hsv, lower_skin, upper_skin)

    # If YCrCb ranges available, compute YCrCb mask and combine
    mask_ycrcb = None
    global lower_skin_ycrcb, upper_skin_ycrcb
    if lower_skin_ycrcb is not None and upper_skin_ycrcb is not None:
        ycrcb = cv2.cvtColor(blur, cv2.COLOR_BGR2YCrCb)
        mask_ycrcb = cv2.inRange(ycrcb, lower_skin_ycrcb, upper_skin_ycrcb)

    if mask_ycrcb is not None:
        mask = cv2.bitwise_or(mask_hsv, mask_ycrcb)
    else:
        mask = mask_hsv

    kernel = np.ones((5, 5), np.uint8)
    # reducing noise
    filtered = cv2.GaussianBlur(mask, (3, 3), 0)
    ret, thresh = cv2.threshold(filtered, 127, 255, 0)  # thresholding the image
    thresh = cv2.GaussianBlur(thresh, (5,5), 0) # reducing the noise
    kernel2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, CONFIG['MORPH_KERNEL_SIZE'])
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel2, iterations=CONFIG['MORPH_ITERATIONS'])
    # finding contours in the image. Will be used later in complex hull algorithm
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    return roi, thresh, contours



def main():
    global hand_hsv, lower_skin, upper_skin, calibration_stage, palm_hsv_range, back_hsv_range
    is_hand_created = False
    capture = cv2.VideoCapture(0)
    # Initialize serial communication with Arduino
    try:
        # arduino = serial.Serial('COM10', 9600, timeout=1)
        arduino = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
        time.sleep(5)  # Wait for Arduino to reset
        print("Serial connection to Arduino established.")
    except Exception as e:
        arduino = None
        print(f"Could not connect to Arduino: {e}")

    while capture.isOpened():
        pressed_key = cv2.waitKey(1)
        _, frame = capture.read()
        frame = cv2.flip(frame, 1)
        frame_copy = frame.copy()
        frame_copy = crop_center(frame_copy)

        # Calibration key handler
        if pressed_key & 0xFF == ord('z') or pressed_key & 0xFF == ord('Z'):
            if calibration_stage == 0:
                # First calibration - PALM
                palm_hsv_range = hand_hsv_func(frame_copy, "palm")
                palm_ycrcb_range = hand_ycrcb_func(frame_copy, "palm")
                calibration_stage = 1
                print("\n>>> PALM calibrated! Now show BACK of hand and press 'z' again <<<\n")
            elif calibration_stage == 1:
                # Second calibration - BACK of hand
                back_hsv_range = hand_hsv_func(frame_copy, "back")
                back_ycrcb_range = hand_ycrcb_func(frame_copy, "back")
                calibration_stage = 2
                # Combine both ranges for HSV and YCrCb
                lower_skin, upper_skin = combine_hsv_ranges(palm_hsv_range, back_hsv_range)
                lower_skin_ycrcb, upper_skin_ycrcb = combine_ycrcb_ranges(palm_ycrcb_range, back_ycrcb_range)
                is_hand_created = True
                print("\n>>> Both sides calibrated! Hand detection active <<<\n")
        
        # Reset calibration
        if pressed_key & 0xFF == ord('r'):
            is_hand_created = False
            calibration_stage = 0
            palm_hsv_range = None
            back_hsv_range = None
            lower_skin = None
            upper_skin = None
            finger_count_history.clear()  # Clear anti-flicker history
            print("\n>>> Recalibration mode - Press 'z' to calibrate PALM <<<\n")

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

            # Get segmentation results
            roi, thresh, contours = imageFiltering(frame_copy_clean, lower_skin, upper_skin)

            # Extract hand centroid and validation directly from segmentation
            hand_centroid_cropped = None
            is_hand = False

            if len(contours) > 0:
                # Find largest contour
                max_contour = max(contours, key=cv2.contourArea)
                
                # Validate if it's a hand
                is_hand, validation_msg = validate_hand_contour(max_contour, frame_copy_clean)
                
                if is_hand:
                    # Calculate centroid
                    hand_centroid_cropped = centroid(max_contour)
                    
                    if hand_centroid_cropped is not None:
                        # Draw purple centroid on frame_copy
                        cv2.circle(frame_copy, hand_centroid_cropped, 5, [255, 0, 255], -1)
                        cv2.putText(frame_copy, "HAND DETECTED", (10, 30), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                else:
                    # Show validation message
                    cv2.putText(frame_copy, validation_msg, (10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Calculate distance if hand is detected
            if hand_centroid_cropped is not None and is_hand:
                # === SEND TO ARDUINO ===
                # if arduino:
                #     # Send as "X:val,Y:val\n"
                #     msg = f"X:{hand_centroid_cropped[0]},Y:{hand_centroid_cropped[1]}\n"
                #     try:
                #         arduino.write(msg.encode())
                #     except Exception as e:
                #         print(f"Serial send error: {e}")
                
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
                
                # Blank image for contour visualization
                drawing = np.zeros(roi.shape, np.uint8)
                
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
                        cv2.line(drawing, hand_centroid_cropped, highest_point, [255, 255, 0], 1)  # Cyan line
                        
                        # Within range or not calibrated yet - proceed with detection
                        # Draw contours
                        cv2.drawContours(drawing, [contour], -1, (0, 255, 0), 0)
                        
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
                                min_fingertip_distance = CONFIG['MIN_FINGERTIP_DIST']
                                angle_min, angle_max = CONFIG['ANGLE_RANGE']
                                    
                                if (angle >= angle_min and angle <= angle_max and d > CONFIG['DEFECT_DEPTH_THRESHOLD'] and 
                                    dist_to_start > min_fingertip_distance and dist_to_end > min_fingertip_distance and
                                    y_diff_start < 0 and y_diff_end < 0):
                                    count_defects += 1
                                    # Draw defect visualization
                                    cv2.circle(drawing, far, 5, [0, 0, 255], -1)  # Red circle at valley point
                                    cv2.line(drawing, hand_centroid_cropped, start, [0, 255, 255], 1)  # Cyan line to start
                                    cv2.line(drawing, hand_centroid_cropped, end, [0, 255, 255], 1)  # Cyan line to end
                                
                                cv2.line(drawing, start, end, [0, 100, 0], 2)
                        
                        # Distinguish FIST from real fingers using highest point distance
                        min_one_finger_distance = CONFIG['MIN_ONE_FINGER_DIST']
                        
                        # Determine raw finger count
                        raw_finger_count = -1  # -1 = FIST, 0 = undetermined, 1-5 = finger count
                        
                        if count_defects == 0:
                            # No defects detected
                            if highest_point_distance > min_one_finger_distance:
                                # Highest point far from centroid = ONE finger extended
                                raw_finger_count = 1
                            else:
                                # Highest point close to centroid = FIST
                                raw_finger_count = -1
                        
                        elif count_defects >= 1:
                            # Advanced shadow vs real finger detection using:
                            # 1. Area ratio - FIST has higher ratio (contour fills hull more)
                            # 2. Highest point distance - Real fingers extend far from centroid
                            # 3. Defect count - Shadows rarely create many deep defects
                            
                            # Thresholds for shadow detection
                            SHADOW_AREA_RATIO_THRESHOLD = 75.0  # FIST typically > 75%
                            SHADOW_DISTANCE_THRESHOLD = 80     # More conservative than ONE finger threshold
                            
                            # Check if it's a FIST with shadow artifacts
                            is_likely_fist_shadow = (
                                area_ratio > SHADOW_AREA_RATIO_THRESHOLD and 
                                highest_point_distance < SHADOW_DISTANCE_THRESHOLD
                            ) or (
                                # Alternative: very high area ratio even with moderate distance
                                area_ratio > 85.0 and 
                                highest_point_distance < min_one_finger_distance
                            )
                            
                            if is_likely_fist_shadow:
                                # FIST with shadow artifacts
                                raw_finger_count = -1
                            else:
                                # Real extended fingers detected
                                raw_finger_count = count_defects + 1  # defects + 1 = finger count
                        
                        # Apply anti-flicker filter to stabilize detection
                        stable_finger_count = get_stable_finger_count(raw_finger_count)
                        
                        # Display results based on stable count
                        if stable_finger_count == -1:
                            # FIST detected
                            cv2.putText(drawing, "FIST detected", (10, 90),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                            # Send 'S' to Arduino
                            if arduino:
                                try:
                                    arduino.write(b'S\n')
                                except Exception as e:
                                    print(f"Serial send error: {e}")
                        elif stable_finger_count == 1:
                            # ONE finger
                            cv2.line(drawing, hand_centroid_cropped, highest_point, [255, 255, 0], 1)
                            cv2.putText(drawing, "One finger detected", (10, 90),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                            # Calculate error_x and error_y (centroid to center of cropped frame)
                            error_x = hand_centroid_cropped[0] - center_x
                            error_y = hand_centroid_cropped[1] - center_y
                            # Send 'F' and error values to Arduino
                            if arduino:
                                msg = f"F,{error_x},{error_y}\n"
                                try:
                                    arduino.write(msg.encode())
                                    
                                except Exception as e:
                                    print(f"Serial send error: {e}")
                        elif stable_finger_count == 2:
                            cv2.putText(drawing, "Two fingers detected", (10, 90),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                            # Send 'T' to Arduino for two fingers
                            if arduino:
                                try:
                                    arduino.write(b'M\n')
                                    # time.sleep(0.05)  # Short delay
                                    # response = arduino.readline().decode().strip()
                                    # print(f"Arduino response for two fingers: '{response}'")
                                except Exception as e:
                                    print(f"Serial send error: {e}")
                        elif stable_finger_count == 3:
                            cv2.putText(drawing, "Three fingers detected", (10, 90),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                            # Send 'L' to Arduino for three fingers
                            if arduino:
                                try:
                                    arduino.write(b'B\n')
                                except Exception as e:
                                    print(f"Serial send error: {e}")
                        elif stable_finger_count == 4:
                            cv2.putText(drawing, "Four fingers detected", (10, 90),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                            # Send 'L' to Arduino for four fingers
                            if arduino:
                                try:
                                    arduino.write(b'L\n')
                                except Exception as e:
                                    print(f"Serial send error: {e}")
                        elif stable_finger_count == 5:
                            cv2.putText(drawing, "Five fingers detected", (10, 90),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                            # Send 'R' to Arduino for five fingers
                            if arduino:
                                try:
                                    arduino.write(b'R\n')
                                except Exception as e:
                                    print(f"Serial send error: {e}")
                    except Exception as e:
                        pass
                cv2.imshow("thresh",thresh)
                cv2.imshow("drawing",drawing)

            else:
                # No hand detected, send 'N' to Arduino
                if arduino:
                    try:
                        arduino.write(b'N\n')
                    except Exception as e:
                        print(f"Serial send error: {e}")
        else:
            frame_copy = rescale_frame(draw_rect_V2(frame_copy))  # Use V2 for cropped frame
            # Show instruction based on calibration stage
            if calibration_stage == 0:
                cv2.putText(frame_copy, "Press 'z' to calibrate PALM (front of hand)", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            elif calibration_stage == 1:
                cv2.putText(frame_copy, "PALM calibrated! Press 'z' for BACK of hand", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                cv2.putText(frame_copy, ">>> FLIP YOUR HAND <<<", (10, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        cv2.imshow("Cropped", frame_copy)
        
        if pressed_key == 27:
            break

    cv2.destroyAllWindows()
    capture.release()

if __name__ == '__main__':
    main()