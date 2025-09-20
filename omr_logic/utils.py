import cv2
import numpy as np

def get_sheet_outline(image):
    """
    Detect the outline/corners of the OMR sheet.
    """
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blurred, 75, 200)
        
        contours, _ = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
        
        for contour in contours:
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
            
            if len(approx) == 4:
                return approx.reshape(4, 2)
        
        h, w = image.shape[:2]
        return np.array([[0, 0], [w, 0], [w, h], [0, h]])
        
    except Exception as e:
        print(f"Error in get_sheet_outline: {e}")
        h, w = image.shape[:2]
        return np.array([[0, 0], [w, 0], [w, h], [0, h]])

def get_warped_image(image, corners):
    """
    Apply perspective transformation.
    """
    try:
        corners = order_points(corners)
        
        width = max(
            np.linalg.norm(corners[1] - corners[0]), 
            np.linalg.norm(corners[2] - corners[3])
        )
        height = max(
            np.linalg.norm(corners[3] - corners[0]), 
            np.linalg.norm(corners[2] - corners[1])
        )
        
        dst = np.array([
            [0, 0],
            [width - 1, 0],
            [width - 1, height - 1],
            [0, height - 1]
        ], dtype=np.float32)
        
        matrix = cv2.getPerspectiveTransform(corners.astype(np.float32), dst)
        warped = cv2.warpPerspective(image, matrix, (int(width), int(height)))
        
        return warped
        
    except Exception as e:
        print(f"Error in get_warped_image: {e}")
        return image

def order_points(pts):
    """Order points: top-left, top-right, bottom-right, bottom-left"""
    rect = np.zeros((4, 2), dtype=np.float32)
    
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    
    return rect

def detect_bubbles(roi):
    """
    Improved bubble detection with better preprocessing.
    """
    try:
        if len(roi.shape) == 3:
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        else:
            gray = roi
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Use adaptive threshold for better results
        thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       cv2.THRESH_BINARY_INV, 11, 2)
        
        # Alternative: Simple threshold (try both)
        # _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        height, width = thresh.shape
        option_width = width // 4
        
        bubble_intensities = []
        for i in range(4):
            x_start = i * option_width
            x_end = (i + 1) * option_width
            option_roi = thresh[:, x_start:x_end]
            
            # Calculate filled percentage
            filled_pixels = np.sum(option_roi == 255)
            total_pixels = option_roi.shape[0] * option_roi.shape[1]
            intensity = filled_pixels / total_pixels if total_pixels > 0 else 0
            
            bubble_intensities.append(intensity)
        
        return bubble_intensities
    
    except Exception as e:
        print(f"Error in detect_bubbles: {e}")
        return [0, 0, 0, 0]