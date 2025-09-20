import cv2
import numpy as np
from .utils import get_sheet_outline, get_warped_image

# Assuming detect_bubbles is a function that processes a small ROI
# and returns a list of pixel intensities for each bubble option.
# You will need to define this in your utils.py or here.
def detect_bubbles(roi):
    # This is a placeholder function. You need to implement your
    # actual bubble detection logic here.
    # For now, it will apply a threshold and count filled pixels.
    
    gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    _, thresh_roi = cv2.threshold(gray_roi, 180, 255, cv2.THRESH_BINARY_INV)
    
    intensities = []
    # Assuming 4 options (A, B, C, D)
    for opt in range(4):
        opt_width = thresh_roi.shape[1] // 4
        opt_roi = thresh_roi[:, opt * opt_width: (opt + 1) * opt_width]
        intensities.append(np.sum(opt_roi) / 255)
        
    return intensities

def generate_bubble_coordinates(sheet_width=800, sheet_height=1000):
    """
    Generate bubble coordinates for a standard OMR sheet layout.
    Adjust these values based on your actual OMR sheet layout.
    """
    bubble_coords = []
    
    # Configuration for bubble layout - ADJUST THESE VALUES
    start_x = 50 
    start_y = 100 
    question_height = 30
    subject_width = 160
    bubble_width = 140
    bubble_height = 20
    
    for subject in range(5):
        x_pos = start_x + (subject * subject_width)
        
        for question in range(20):
            y_pos = start_y + (question * question_height)
            
            bubble_coords.append({
                'x': x_pos,
                'y': y_pos, 
                'width': bubble_width,
                'height': bubble_height
            })
    
    return bubble_coords

def evaluate_omr_sheet(image_path, answer_key):
    """
    Evaluates a single OMR sheet image using a dictionary-based answer key.
    """
    print(f"Evaluating sheet: {image_path}")
    print(f"Answer key: {list(answer_key.keys())}")
    
    # Use a fixed list of subject names based on the answer_key dictionary
    subject_names = list(answer_key.keys())
    
    # Initialize scores_by_subject with subject names
    scores_by_subject = {name: 0 for name in subject_names}
    total_correct = 0
    
    try:
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image from {image_path}")
        
        print(f"Image loaded successfully. Shape: {image.shape}")
        
        corners = get_sheet_outline(image)
        if corners is None:
            return {'error': 'Invalid document. OMR sheet not detected.'}, None
        
        warped = get_warped_image(image, corners)
        print("Applied perspective correction")
        
        bubble_coords = generate_bubble_coordinates(warped.shape[1], warped.shape[0])
        print(f"Generated {len(bubble_coords)} bubble coordinates")
        
        FILL_THRESHOLD = 0.05
        
        for i, bubble_coord in enumerate(bubble_coords):
            # Check if we have an answer for this question
            if i >= 100:  # Assuming 100 questions total
                break
            
            x, y, w, h = bubble_coord['x'], bubble_coord['y'], bubble_coord['width'], bubble_coord['height']
            
            x = max(0, min(x, warped.shape[1] - w))
            y = max(0, min(y, warped.shape[0] - h))
            w = min(w, warped.shape[1] - x)
            h = min(h, warped.shape[0] - y)
            
            roi = warped[y:y+h, x:x+w]
            
            if roi.size == 0:
                continue
            
            try:
                bubble_intensities = detect_bubbles(roi)
                max_intensity = max(bubble_intensities)
                detected_answer = bubble_intensities.index(max_intensity)
                
                # Check for a sufficiently filled bubble
                if max_intensity > FILL_THRESHOLD:
                    # Map question index to subject and question number within that subject
                    subject_index = i // 20
                    subject_name = subject_names[subject_index]
                    question_in_subject_index = i % 20
                    
                    correct_answer = answer_key[subject_name][question_in_subject_index]
                    
                    if detected_answer == correct_answer:
                        scores_by_subject[subject_name] += 1
                        total_correct += 1
                        
                    print(f"Q{i+1}: Detected={chr(65+detected_answer)}, "
                          f"Correct={chr(65+correct_answer)}, "
                          f"Match={'✓' if detected_answer == correct_answer else '✗'}, "
                          f"Intensity={max_intensity:.3f}")
                else:
                    print(f"Q{i+1}: No clear answer detected (max intensity: {max_intensity:.3f})")

            except Exception as e:
                print(f"Error processing question {i+1}: {str(e)}")
                continue
        
        print(f"\nEvaluation Complete:")
        print(f"Total correct: {total_correct}/100")
        print(f"Scores by subject: {scores_by_subject}")
        
        return scores_by_subject, total_correct
        
    except Exception as e:
        print(f"Error in evaluate_omr_sheet: {str(e)}")
        import traceback
        traceback.print_exc()
        
        scores_by_subject = {name: 0 for name in subject_names}
        return {'error': str(e)}, 0