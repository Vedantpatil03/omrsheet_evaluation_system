import streamlit as st
import requests
import json

st.set_page_config(page_title="OMR Evaluation", layout="centered")
st.title("Automated OMR Evaluation System")



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
    version = st.selectbox("Exam Version", versions if versions else ["--"])
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
        
        # Data sent to the backend remains simplified as per your previous request
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

                        st.subheader("Subject-wise Scores")
                        scores = result.get("scores", {})
                        
                        # --- MODIFICATION STARTS HERE ---
                        # Get the default subject questions per subject from the answer key.
                        # Assuming all subjects in a given version have the same number of questions.
                        # You can make this dynamic if subjects have different question counts.
                        default_qps = 20 # This was hardcoded in your previous request
                        
                        # Fetch the actual answer key for the selected version to get correct question counts
                        # This would require another API call or a modification to the /api/versions endpoint
                        # For now, let's keep it simple and assume 20 questions per subject based on your ANSWER_KEYS structure.
                        
                        # Iterate through the scores dictionary directly.
                        # The keys of 'scores' already contain the correct subject names from your Flask backend.
                        for subject_name, score in scores.items():
                            percent = (score / default_qps) * 100 if default_qps else 0
                            c1, c2, c3 = st.columns([3, 1, 1])
                            with c1:
                                st.write(f"{subject_name}") # Use subject_name directly
                            with c2:
                                st.write(f"{score}/{default_qps}")
                            with c3:
                                st.write(f"{percent:.1f}%")
                        # --- MODIFICATION ENDS HERE ---

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
                                 # Footer
st.markdown('''
<div class="footer">
    <p>🎯 <strong>OMR Evaluation System</strong> • Developed by <strong>Vedant Patil</strong></p>

</div>
''', unsafe_allow_html=True)