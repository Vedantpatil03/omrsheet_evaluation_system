import streamlit as st
import requests
import json

st.set_page_config(page_title="OMR Evaluation", layout="centered")
st.title("AUTOMATED OMR EVALUATION SYSTEM")

BACKEND = "http://localhost:5000"

@st.cache_data(ttl=30)
def load_versions():
    try:
        r = requests.get(f"{BACKEND}/api/versions", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        return []

versions = load_versions()

# Display a warning if the backend is not accessible
if not versions:
    st.error("Could not connect to the backend. Please ensure the Flask server is running.")

with st.form("omr_form"):
    student_id = st.text_input("Student ID")
    version = st.selectbox("Paper Code", versions if versions else ["--"])
    uploaded_file = st.file_uploader(
        "Upload OMR Sheet Image",
        type=["jpg", "jpeg", "png", "bmp", "tiff"],
        help="Image of filled OMR sheet."
    )
    submit = st.form_submit_button("Evaluate Sheet")

if submit:
    if not student_id or not uploaded_file or version in ("--", None):
        st.error("All fields required.")
    else:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        data = {
            "student_id": student_id,
            "version": version
        }
        
        with st.spinner("Evaluating..."):
            try:
                resp = requests.post(f"{BACKEND}/api/upload", files=files, data=data, timeout=60)
            except requests.exceptions.RequestException as e:
                st.error(f"Request failed: {e}")
            else:
                if resp.status_code == 200:
                    try:
                        result = resp.json()
                    except json.JSONDecodeError:
                        st.error("Invalid JSON from server.")
                        st.code(resp.text)
                    else:
                        st.success("OMR Sheet Successfully Evaluated!")
                        st.subheader(f"Results for Student ID: {result.get('student_id')}")

                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric(
                                "Total Score",
                                str(result.get("total_score", 0)),
                                f"out of {result.get('max_possible_score', 0)}"
                            )
                        with col2:
                            max_score = result.get("max_possible_score", 1) or 1
                            pct = (result.get("total_score", 0) / max_score) * 100
                            st.metric("Percentage", f"{pct:.1f}%")

                        st.write(f"Sheet Version: {result.get('version')}")

                        if "warnings" in result:
                            for w in result["warnings"]:
                                st.warning(w)

                        # --- Subject-wise scores with CSS ---
                        st.subheader("Subject-wise Scores")

                        # Inject CSS styling
                        
                        st.markdown("""
                            <style>
                            .subject-row {
                                display: flex;
                                justify-content: space-between;
                                padding: 10px;
                                margin-bottom: 8px;
                                border-radius: 8px;
                                background: #f9f9f9;
                                border: 1px solid #ddd;
                            }
                            .subject-row:hover {
                                background: #eef6ff;
                                border-color: #3399ff;
                            }
                                    
                            .subject-name {
                                font-weight: bold;
                                font-size: 16px;
                                color: #333;
                            }
                            .subject-score {
                                font-size: 15px;
                                color: #555;
                                    
                            }
                            </style>
                        """, unsafe_allow_html=True)

                        scores = result.get("scores", {})

                        for subject_name, details in scores.items():
                            # ✅ Handle both dict (new format) and int (old format)
                            if isinstance(details, dict):
                                score = details.get("score", 0)
                                max_q = details.get("max", 20)
                                pct = details.get("percentage", (score / max_q) * 100 if max_q else 0)
                            else:
                                score = details
                                max_q = 20
                                pct = (score / max_q) * 100 if max_q else 0

                            st.markdown(f"""
                            <div class="subject-row">
                                <div class="subject-name">{subject_name}</div>
                                <div class="subject-score">{score} / {max_q}</div>
                                <div class="subject-score">{pct:.1f}%</div>
                            </div>
                            """, unsafe_allow_html=True)

                        with st.expander("Raw Result Data"):
                            st.json(result)
                else:
                    try:
                        err = resp.json()
                    except json.JSONDecodeError:
                        st.error(f"Server Error {resp.status_code}")
                        st.code(resp.text)
                    else:
                        st.error("An error occurred during evaluation.")
                        if "details" in err:
                            st.write(f"Details: {err['details']}")
                        if "suggestions" in err:
                            st.info("Suggestions:")
                            for s in err.get("suggestions", []):
                                st.write(f"- {s}")
                                
st.caption("OMR Evaluation System • Developed by Vedant Patil")