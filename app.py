import os
import sqlite3
import traceback
from datetime import datetime
import cv2
import numpy as np
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from omr_logic.evaluation import evaluate_omr_sheet

# -----------------------------------------------------------------------------
# Flask setup
# -----------------------------------------------------------------------------
app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

DB_PATH = os.path.join(BASE_DIR, "results.db")

# -----------------------------------------------------------------------------
# Answer keys (dict: version -> dict(subject -> list of correct options))
# Each subject here has 20 questions (total 100)
# -----------------------------------------------------------------------------
ANSWER_KEYS = {
    'A': {
        "Python":        [0,1,2,3,0,1,2,3,0,1,2,3,0,1,2,3,0,1,2,3],
        "Data Analysis": [1,2,3,0,1,2,3,0,1,2,3,0,1,2,3,0,1,2,3,0],
        "MySQL":         [2,3,0,1,2,3,0,1,2,3,0,1,2,3,0,1,2,3,0,1],
        "PowerBI":       [3,0,1,2,3,0,1,2,3,0,1,2,3,0,1,2,3,0,1,2],
        "Adv Stats":     [0,2,1,3,0,2,1,3,0,2,1,3,0,2,1,3,0,2,1,3]
    },
    'B': {
        "Python":        [1,0,3,2,1,0,3,2,1,0,3,2,1,0,3,2,1,0,3,2],
        "Data Analysis": [2,1,0,3,2,1,0,3,2,1,0,3,2,1,0,3,2,1,0,3],
        "MySQL":         [3,2,1,0,3,2,1,0,3,2,1,0,3,2,1,0,3,2,1,0],
        "PowerBI":       [0,3,2,1,0,3,2,1,0,3,2,1,0,3,2,1,0,3,2,1],
        "Adv Stats":     [1,3,0,2,1,3,0,2,1,3,0,2,1,3,0,2,1,3,0,2]
    },
    'C': {
        "Python":        [2,3,1,0,2,3,1,0,2,3,1,0,2,3,1,0,2,3,1,0],
        "Data Analysis": [3,0,2,1,3,0,2,1,3,0,2,1,3,0,2,1,3,0,2,1],
        "MySQL":         [0,1,3,2,0,1,3,2,0,1,3,2,0,1,3,2,0,1,3,2],
        "PowerBI":       [1,2,0,3,1,2,0,3,1,2,0,3,1,2,0,3,1,2,0,3],
        "Adv Stats":     [2,0,3,1,2,0,3,1,2,0,3,1,2,0,3,1,2,0,3,1]
    }
}

# -----------------------------------------------------------------------------
# Database helpers
# -----------------------------------------------------------------------------
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                sheet_version TEXT NOT NULL,
                subject1_name TEXT,
                subject2_name TEXT,
                subject3_name TEXT,
                subject4_name TEXT,
                subject5_name TEXT,
                subject1_score INTEGER,
                subject2_score INTEGER,
                subject3_score INTEGER,
                subject4_score INTEGER,
                subject5_score INTEGER,
                total_score INTEGER,
                max_score INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_results_student ON results(student_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_results_version ON results(sheet_version)")
        c.commit()

init_db()

# -----------------------------------------------------------------------------
# Utility functions
# -----------------------------------------------------------------------------
def validate_file_type(file):
    if not file:
        return False, "No file provided"
    if file.filename.strip() == "":
        return False, "Empty filename"
    allowed = {'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'gif'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in allowed:
        return False, f"Invalid file type '{ext}'. Allowed: {', '.join(sorted(allowed))}"
    return True, "Valid"

def basic_image_validation(path):
    try:
        img = cv2.imread(path)
        if img is None:
            return False, "Cannot read image file."
        h, w = img.shape[:2]
        if w < 100 or h < 100:
            return False, f"Image too small ({w}x{h})."
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        mean_val = float(np.mean(gray))
        std_val = float(np.std(gray))
        if std_val < 1:
            return False, "Image appears blank (very low contrast)."
        if mean_val > 254:
            return False, "Image is completely white."
        if mean_val < 1:
            return False, "Image is completely black."
        return True, f"OK (size {w}x{h}, brightness {mean_val:.0f})"
    except Exception as e:
        return False, f"Image validation error: {e}"

def flatten_answer_key(subject_key_dict):
    flat = []
    names = []
    lengths = []
    for name, seq in subject_key_dict.items():
        names.append(name)
        lengths.append(len(seq))
        flat.extend(seq)
    return flat, names, lengths

def aggregate_subject_scores(per_question_scores, lengths, names):
    out = {}
    idx = 0
    for name, ln in zip(names, lengths):
        segment = per_question_scores[idx:idx+ln]
        out[name] = int(sum(segment))
        idx += ln
    return out

def row_to_dict(row: sqlite3.Row):
    subjects = []
    for i in range(1, 6):
        n = row.get(f"subject{i}_name") if hasattr(row, "get") else row[f"subject{i}_name"]
        s = row.get(f"subject{i}_score") if hasattr(row, "get") else row[f"subject{i}_score"]
        if n:
            subjects.append({"name": n, "score": s})
    return {
        "id": row["id"],
        "student_id": row["student_id"],
        "version": row["sheet_version"],
        "subjects": subjects,
        "total_score": row["total_score"],
        "max_score": row["max_score"],
        "created_at": row["created_at"]
    }

# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@app.route("/")
def health():
    return jsonify({"message": "OMR Evaluation System API", "status": "running"})

@app.route("/api/versions")
def get_versions():
    return jsonify(list(ANSWER_KEYS.keys()))

@app.route("/api/upload", methods=["POST"])
def upload_sheet():
    filepath = None
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded", "error_type": "VALIDATION_ERROR"}), 400
        file = request.files['file']

        ok, msg = validate_file_type(file)
        if not ok:
            return jsonify({
                "error": "Invalid file type",
                "error_type": "FILE_TYPE_ERROR",
                "details": msg
            }), 400

        student_id = request.form.get("student_id")
        version = request.form.get("version")

        if not student_id or not version:
            return jsonify({
                "error": "Missing required information",
                "error_type": "VALIDATION_ERROR",
                "details": "student_id and version required"
            }), 400

        if version not in ANSWER_KEYS:
            return jsonify({
                "error": "Invalid exam version",
                "error_type": "VALIDATION_ERROR",
                "details": f"Version '{version}' not found"
            }), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        img_ok, img_msg = basic_image_validation(filepath)
        if not img_ok:
            return jsonify({
                "error": "Invalid Image",
                "error_type": "INVALID_IMAGE",
                "details": img_msg
            }), 400

        answer_key_dict = ANSWER_KEYS[version]
        flat_key, subject_names, lengths = flatten_answer_key(answer_key_dict)

        # Evaluate (prefer flat list)
        try:
            per_question_scores, total_score = evaluate_omr_sheet(filepath, flat_key)
        except Exception:
            # Fallback: try with dict if implementation expects dict
            try:
                per_question_scores, total_score = evaluate_omr_sheet(filepath, answer_key_dict)
            except Exception as eval_err:
                return jsonify({
                    "error": "OMR Processing Failed",
                    "error_type": "EVALUATION_ERROR",
                    "details": str(eval_err)
                }), 500

        # Normalize per_question_scores => list of ints 0/1
        if isinstance(per_question_scores, dict):
            # If dict mapping question index -> 0/1
            per_question_scores = [
                per_question_scores[i] for i in sorted(per_question_scores.keys())
            ]
        if not isinstance(per_question_scores, list):
            return jsonify({
                "error": "EVALUATION_FORMAT_ERROR",
                "details": "evaluate_omr_sheet must return (list[int], int) or compatible."
            }), 500

        # Aggregate
        subject_scores = aggregate_subject_scores(per_question_scores, lengths, subject_names)

        total_questions = len(flat_key)

        # DB insert (pad/truncate to 5 subjects)
        subject_names_padded = subject_names[:5] + [None] * (5 - len(subject_names))
        subject_scores_ordered = [subject_scores.get(n, 0) if n else 0 for n in subject_names_padded]

        with get_conn() as c:
            c.execute("""
                INSERT INTO results (
                    student_id, sheet_version,
                    subject1_name, subject2_name, subject3_name, subject4_name, subject5_name,
                    subject1_score, subject2_score, subject3_score, subject4_score, subject5_score,
                    total_score, max_score
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                student_id, version,
                subject_names_padded[0], subject_names_padded[1], subject_names_padded[2],
                subject_names_padded[3], subject_names_padded[4],
                subject_scores_ordered[0], subject_scores_ordered[1], subject_scores_ordered[2],
                subject_scores_ordered[3], subject_scores_ordered[4],
                int(total_score), total_questions
            ))
            c.commit()

        warnings = []
        if total_score == 0:
            warnings.append("No correct answers detected.")
        elif total_score < 5:
            warnings.append("Very low score detected.")

        resp = {
            "student_id": student_id,
            "version": version,
            "scores": subject_scores,
            "total_score": int(total_score),
            "max_possible_score": total_questions,
            "evaluation_status": "success",
            "image_info": img_msg,
            "subject_order": subject_names,
            "raw_question_scores": per_question_scores
        }
        if warnings:
            resp["warnings"] = warnings
        return jsonify(resp)

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "error": "System Error",
            "error_type": "PROCESSING_ERROR",
            "details": str(e)
        }), 500
    finally:
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass

# -----------------------------------------------------------------------------
# Results listing (pagination)
# -----------------------------------------------------------------------------
@app.route("/api/results", methods=["GET"])
def list_results():
    try:
        limit = int(request.args.get("limit", 20))
        offset = int(request.args.get("offset", 0))
        student_id = request.args.get("student_id")
        version = request.args.get("version")

        limit = max(1, min(limit, 100))
        offset = max(0, offset)

        conditions = []
        params = []
        if student_id:
            conditions.append("student_id = ?")
            params.append(student_id)
        if version:
            conditions.append("sheet_version = ?")
            params.append(version)
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

        query = f"""
            SELECT *
            FROM results
            {where_clause}
            ORDER BY created_at DESC, id DESC
            LIMIT ? OFFSET ?
        """
        params_with_page = params + [limit, offset]

        with get_conn() as c:
            rows = c.execute(query, params_with_page).fetchall()
            total = c.execute(f"SELECT COUNT(*) FROM results {where_clause}", params).fetchone()[0]

        data = [row_to_dict(r) for r in rows]
        return jsonify({
            "count": len(data),
            "total": total,
            "limit": limit,
            "offset": offset,
            "results": data
        })
    except Exception as e:
        return jsonify({"error": "LIST_FAILED", "details": str(e)}), 500

# -----------------------------------------------------------------------------
# Results for a single student
# -----------------------------------------------------------------------------
@app.route("/api/results/<student_id>", methods=["GET"])
def results_for_student(student_id):
    try:
        with get_conn() as c:
            rows = c.execute(
                "SELECT * FROM results WHERE student_id = ? ORDER BY created_at DESC, id DESC",
                (student_id,)
            ).fetchall()
        return jsonify({
            "student_id": student_id,
            "attempts": len(rows),
            "results": [row_to_dict(r) for r in rows]
        })
    except Exception as e:
        return jsonify({"error": "STUDENT_RESULTS_FAILED", "details": str(e)}), 500

# -----------------------------------------------------------------------------
# Run
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)