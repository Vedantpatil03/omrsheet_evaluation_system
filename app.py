import os
import traceback
import cv2
import numpy as np
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from omr_logic.evaluation import evaluate_omr_sheet
import sqlite3

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Answer keys with subject names as keys
ANSWER_KEYS = {
    'A': {
        "Python": [0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3],
        "Data Analysis": [1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0],
        "MySQL": [2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1],
        "PowerBI": [3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2],
        "Adv Stats": [0, 2, 1, 3, 0, 2, 1, 3, 0, 2, 1, 3, 0, 2, 1, 3, 0, 2, 1, 3]
    },
    'B': {
        "Python": [1, 0, 3, 2, 1, 0, 3, 2, 1, 0, 3, 2, 1, 0, 3, 2, 1, 0, 3, 2],
        "Data Analysis": [2, 1, 0, 3, 2, 1, 0, 3, 2, 1, 0, 3, 2, 1, 0, 3, 2, 1, 0, 3],
        "MySQL": [3, 2, 1, 0, 3, 2, 1, 0, 3, 2, 1, 0, 3, 2, 1, 0, 3, 2, 1, 0],
        "PowerBI": [0, 3, 2, 1, 0, 3, 2, 1, 0, 3, 2, 1, 0, 3, 2, 1, 0, 3, 2, 1],
        "Adv Stats": [1, 3, 0, 2, 1, 3, 0, 2, 1, 3, 0, 2, 1, 3, 0, 2, 1, 3, 0, 2]
    },
    'C': {
        "Python": [2, 3, 1, 0, 2, 3, 1, 0, 2, 3, 1, 0, 2, 3, 1, 0, 2, 3, 1, 0],
        "Data Analysis": [3, 0, 2, 1, 3, 0, 2, 1, 3, 0, 2, 1, 3, 0, 2, 1, 3, 0, 2, 1],
        "MySQL": [0, 1, 3, 2, 0, 1, 3, 2, 0, 1, 3, 2, 0, 1, 3, 2, 0, 1, 3, 2],
        "PowerBI": [1, 2, 0, 3, 1, 2, 0, 3, 1, 2, 0, 3, 1, 2, 0, 3, 1, 2, 0, 3],
        "Adv Stats": [2, 0, 3, 1, 2, 0, 3, 1, 2, 0, 3, 1, 2, 0, 3, 1, 2, 0, 3, 1]
    }
}

def get_db_connection():
    conn = sqlite3.connect('results.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            sheet_version TEXT NOT NULL,
            subject1_score INTEGER,
            subject2_score INTEGER,
            subject3_score INTEGER,
            subject4_score INTEGER,
            subject5_score INTEGER,
            total_score INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    conn.close()

def validate_file_type(file):
    if not file:
        return False, "No file provided"
    
    if file.filename == '':
        return False, "Empty filename"
    
    allowed_extensions = {'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'gif'}
    file_ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
    
    if file_ext not in allowed_extensions:
        return False, f"Invalid file type '{file_ext}'. Allowed formats: JPG, JPEG, PNG, BMP, TIFF"
    
    return True, "Valid file type"

def basic_image_validation(filepath):
    try:
        image = cv2.imread(filepath)
        if image is None:
            return False, "Cannot read image file. File may be corrupted."
        
        height, width = image.shape[:2]
        
        if width < 100 or height < 100:
            return False, f"Image too small ({width}x{height}). Please use a larger image."
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        mean_intensity = np.mean(gray)
        std_intensity = np.std(gray)
        
        if std_intensity < 1:
            return False, "Image appears to be completely uniform (no content detected)."
        
        if mean_intensity > 254:
            return False, "Image is completely white."
        
        if mean_intensity < 1:
            return False, "Image is completely black."
        
        return True, f"Image accepted for processing (size: {width}x{height}, brightness: {mean_intensity:.0f})"
    except Exception as e:
        return False, f"Error processing image: {str(e)}"

@app.route('/')
def index():
    return jsonify({'message': 'OMR Evaluation System API', 'status': 'running'})

@app.route('/api/versions')
def get_versions():
    try:
        return jsonify(list(ANSWER_KEYS.keys()))
    except Exception as e:
        app.logger.error(f"Error in get_versions: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_sheet():
    filepath = None
    try:
        print("Upload request received")
        
        if 'file' not in request.files:
            return jsonify({
                'error': 'No file uploaded',
                'error_type': 'VALIDATION_ERROR',
                'suggestions': ['Please select an image file to upload']
            }), 400
        
        file = request.files['file']
        
        is_valid_type, type_message = validate_file_type(file)
        if not is_valid_type:
            return jsonify({
                'error': 'Invalid file type',
                'error_type': 'FILE_TYPE_ERROR',
                'details': type_message,
                'suggestions': [
                    'Upload a valid image file (JPG, PNG, BMP, TIFF)',
                    'Ensure the file extension is correct'
                ]
            }), 400

        student_id = request.form.get('student_id')
        version = request.form.get('version')
        
        if not student_id or not version:
            return jsonify({
                'error': 'Missing required information',
                'error_type': 'VALIDATION_ERROR',
                'details': 'Both student ID and version are required'
            }), 400
        
        if version not in ANSWER_KEYS:
            return jsonify({
                'error': 'Invalid exam version',
                'error_type': 'VALIDATION_ERROR',
                'details': f'Version "{version}" not found'
            }), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        print(f"File saved: {filepath}")
        
        is_valid_image, validation_message = basic_image_validation(filepath)
        print(f"Validation result: {is_valid_image}, Message: {validation_message}")
        
        if not is_valid_image:
            return jsonify({
                'error': 'Invalid Image',
                'error_type': 'INVALID_IMAGE',
                'details': validation_message,
                'student_id': student_id,
                'version': version,
                'suggestions': [
                    'Please upload a clear, readable image',
                    'Ensure the image is not corrupted',
                    'Try taking a new photo with better quality',
                    'Make sure the image file is valid'
                ]
            }), 400
        
        answer_key = ANSWER_KEYS.get(version)
        print(f"Processing evaluation for student: {student_id}, version: {version}")
        
        try:
            scores, total_score = evaluate_omr_sheet(filepath, answer_key)
            print(f"Evaluation completed successfully - Total score: {total_score}")
            
        except Exception as eval_error:
            print(f"Evaluation error: {eval_error}")
            print(traceback.format_exc())
            
            return jsonify({
                'error': 'OMR Processing Failed',
                'error_type': 'EVALUATION_ERROR',
                'details': f'Could not evaluate the OMR sheet: {str(eval_error)}',
                'student_id': student_id,
                'version': version,
                'suggestions': [
                    'Make sure the image shows a complete OMR sheet',
                    'Ensure bubbles are clearly visible and properly filled',
                    'Check that the image is not rotated or skewed',
                    'Try uploading a clearer image of the OMR sheet',
                    'Verify that the sheet contains the expected bubble pattern'
                ]
            }), 500
        
        # --- FIX: MAP SUBJECT NAMES TO GENERIC DB COLUMNS ---
        subject_names = list(answer_key.keys())
        # The correct way to prepare scores for the database insertion
        subject_scores_list = [scores.get(name) for name in subject_names]

        conn = get_db_connection()
        conn.execute('INSERT INTO results (student_id, sheet_version, subject1_score, subject2_score, subject3_score, subject4_score, subject5_score, total_score) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                     (student_id, version, *subject_scores_list, total_score))
        conn.commit()
        conn.close()

        warnings = []
        if total_score == 0:
            warnings.append("No correct answers detected - please verify the answer key or bubble filling")
        elif total_score < 5:
            warnings.append("Very low score detected - please check if bubbles are properly filled")
        
        # FIX: Correctly calculate the max possible score by summing the lengths of all subject lists
        total_questions = sum(len(q_list) for q_list in answer_key.values())

        response_data = {
            'student_id': student_id,
            'version': version,
            'scores': scores,
            'total_score': total_score,
            'max_possible_score': total_questions,
            'evaluation_status': 'success',
            'image_info': validation_message
        }
        
        if warnings:
            response_data['warnings'] = warnings
            
        print(f"Returning successful response: {response_data}")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Unexpected exception occurred: {str(e)}")
        print(traceback.format_exc())
        
        return jsonify({
            'error': 'System Error',
            'error_type': 'PROCESSING_ERROR',
            'details': str(e),
            'suggestions': [
                'Try uploading the image again',
                'Ensure the image file is not corrupted',
                'Contact support if the problem persists'
            ]
        }), 500
        
    finally:
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
                print(f"Cleaned up file: {filepath}")
            except Exception as cleanup_error:
                print(f"Failed to cleanup file {filepath}: {cleanup_error}")

if __name__ == '__main__':
    # Initialize the database when the app starts
    init_db() 
    app.run(debug=True, port=5000)