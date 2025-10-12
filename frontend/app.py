import streamlit as st
import requests
import base64
import os
import openpyxl
import time
# Get project root (2 levels up from app.py in frontend/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORTS_DIR = os.path.join(PROJECT_ROOT, "exports")
os.makedirs(EXPORTS_DIR, exist_ok=True)


# --------------------------
# Session state defaults
# --------------------------
if "step" not in st.session_state:
    st.session_state.step = 1
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []
if "uploaded_paths" not in st.session_state:
    st.session_state.uploaded_paths = []
if "jd_text" not in st.session_state:
    st.session_state.jd_text = ""
if "weights" not in st.session_state:
    st.session_state.weights = {
        "skills": 0.4,
        "experience": 0.3,
        "education": 0.2,
        "certifications": 0.1
    }
if "save_mode" not in st.session_state:
    st.session_state.save_mode = "new_file"
if "results" not in st.session_state:
    st.session_state.results = None
if "excel_file" not in st.session_state:
    st.session_state.excel_file = None
if "excel_file_path" not in st.session_state:
    st.session_state.excel_file_path = None
if "excel_sheet_name" not in st.session_state:
    st.session_state.excel_sheet_name = None
if "export_option" not in st.session_state:
    st.session_state.export_option = "new_file"

# --------------------------
# Title
# --------------------------
st.title("Resume Scanner System")

# --------------------------
# Step 1: Upload Resumes
# --------------------------
if st.session_state.step == 1:
    st.header("Step 1: Upload Resume Files")
    uploaded_files = st.file_uploader(
        "Upload resumes (PDF/DOCX)", type=["pdf", "docx"], accept_multiple_files=True
    )

    if uploaded_files:
        st.session_state.uploaded_files = uploaded_files
        if st.button("Upload Resume(s)"):
            files_data = [("files", (file.name, file.getvalue())) for file in uploaded_files]
            response = requests.post("http://127.0.0.1:8000/upload_resumes_only", files=files_data)
            if response.status_code == 200:
                st.session_state.uploaded_paths = response.json()["uploaded_paths"]
                st.success("✅ Resume(s) uploaded successfully!")
                st.session_state.step = 2
            else:
                st.error(f"Failed to upload resumes: {response.text}")

# --------------------------
# Step 2: JD & Weights
# --------------------------
if st.session_state.step == 2:
    st.header("Step 2: Enter Job Description & Adjust Weights")

    example_jd = """Title: Data Scientist
Skills: Python, Machine Learning, SQL, Data Analysis
Education: B.Tech in IT
Experience: 2 years
Responsibilities: Build ML models, Analyze datasets
Certifications: AWS Machine Learning Foundations"""

    jd_text = st.text_area(
        "Paste Job Description here",
        value=st.session_state.jd_text or example_jd,
        height=200
    )
    st.session_state.jd_text = jd_text

    st.subheader("Weights (adjust using sliders)")
    st.session_state.weights["skills"] = st.slider("Skills Weight", 0.0, 1.0, st.session_state.weights["skills"], 0.05)
    st.session_state.weights["experience"] = st.slider("Experience Weight", 0.0, 1.0, st.session_state.weights["experience"], 0.05)
    st.session_state.weights["education"] = st.slider("Education Weight", 0.0, 1.0, st.session_state.weights["education"], 0.05)
    st.session_state.weights["certifications"] = st.slider("Certifications Weight", 0.0, 1.0, st.session_state.weights["certifications"], 0.05)

    if st.button("Evaluate Resume(s)"):
        if not st.session_state.uploaded_paths or not jd_text.strip():
            st.warning("Please upload resumes and enter JD before proceeding.")
        else:
            params = {
                "jd_text": jd_text,
                "skills_weight": st.session_state.weights["skills"],
                "experience_weight": st.session_state.weights["experience"],
                "education_weight": st.session_state.weights["education"],
                "certifications_weight": st.session_state.weights["certifications"]
            }
            response = requests.post("http://127.0.0.1:8000/upload_jd", params=params)
            if response.status_code == 200:
                st.session_state.jd_data = response.json()["jd_data"]
                st.session_state.step = 3
            else:
                st.error(f"Failed to upload JD: {response.text}")

# --------------------------
# Step 3: Evaluation
# --------------------------
if st.session_state.step == 3:
    st.header("Step 3: Evaluating Resumes...")

    if "evaluation_done" not in st.session_state:
        st.session_state.evaluation_done = False
        st.session_state.evaluation_response = None

    if not st.session_state.evaluation_done:
        with st.spinner("⏳ Evaluating resumes... This may take a few minutes."):
            try:
                response = requests.post(
                    "http://127.0.0.1:8000/evaluate_resumes",
                    json={
                        "uploaded_paths": st.session_state.uploaded_paths,
                        "jd_data": st.session_state.jd_data
                    }
                )
                st.session_state.evaluation_response = response
                st.session_state.evaluation_done = True
            except Exception as e:
                st.error(f"⚠️ Request failed: {e}")
                st.stop()

    # Handle backend response
    response = st.session_state.evaluation_response

    if response.status_code == 200:
        st.session_state.results = response.json()["data"]
        st.success("✅ Evaluation completed successfully!")
        st.session_state.step = 4
    else:
        st.error(f"❌ Evaluation failed: {response.text}")




# --------------------------
# Step 4: Display Results 
# --------------------------
if st.session_state.step >= 4 and st.session_state.results:
    st.header("Step 4: Evaluation Results")

    for resume in st.session_state.results:
        name = resume.get("name", "Unnamed Candidate")
        with st.expander(f"▶ {name}"):
            st.markdown(f"**Email:** {resume.get('email','')}")
            st.markdown(f"**Phone:** {resume.get('phone','')}")
            st.markdown(f"**Location:** {resume.get('location','')}")
            
            urls = resume.get("urls", [])
            if isinstance(urls, list) and urls:
                st.markdown("**URLs:**")
                for url in urls:
                    st.markdown(f"- {url}")

            skills = resume.get("skills", [])
            if skills:
                st.markdown("**Skills:**")
                skill_cards = " ".join([
                    f"<span style='display:inline-block;background:#e0f7fa;color:#006064;"
                    f"padding:5px 10px;margin:3px;border-radius:8px'>{s}</span>"
                    for s in skills
                ])
                st.markdown(skill_cards, unsafe_allow_html=True)

            education = resume.get("education", [])
            if education:
                st.markdown("**Education:**")
                edu_cards = " ".join([
                    f"<span style='display:inline-block;background:#f1f8e9;color:#33691e;"
                    f"padding:5px 10px;margin:3px;border-radius:8px'>"
                    f"{edu.get('degree','')} - {edu.get('institution','')} ({edu.get('year','')})</span>"
                    for edu in education if isinstance(edu, dict)
                ])
                st.markdown(edu_cards, unsafe_allow_html=True)

            experience = resume.get("experience", [])
            if experience:
                st.markdown("**Experience:**")
                exp_cards = " ".join([
                    f"<span style='display:inline-block;background:#fff3e0;color:#e65100;"
                    f"padding:5px 10px;margin:3px;border-radius:8px'>"
                    f"{exp.get('role','')} at {exp.get('company','')} "
                    f"({exp.get('start_date','')} - {exp.get('end_date','')})</span>"
                    for exp in experience if isinstance(exp, dict)
                ])
                st.markdown(exp_cards, unsafe_allow_html=True)

            projects = resume.get("projects", [])
            if projects:
                st.markdown("**Projects:**")
                proj_cards = " ".join([
                    f"<span style='display:inline-block;background:#f3e5f5;color:#4a148c;"
                    f"padding:5px 10px;margin:3px;border-radius:8px'>"
                    f"{proj.get('title','')} [{', '.join(proj.get('technologies',[]))}]: "
                    f"{proj.get('description','')}</span>"
                    for proj in projects if isinstance(proj, dict)
                ])
                st.markdown(proj_cards, unsafe_allow_html=True)

            certs = resume.get("certifications", [])
            if certs:
                st.markdown("**Certifications:**")
                cert_cards = " ".join([
                    f"<span style='display:inline-block;background:#ede7f6;color:#311b92;"
                    f"padding:5px 10px;margin:3px;border-radius:8px'>{c}</span>"
                    for c in certs
                ])
                st.markdown(cert_cards, unsafe_allow_html=True)

        # --------------------------
        # ✅ Summary Section (Styled)
        # --------------------------
                st.markdown("---")
                st.markdown("### 📊 Summary")

                # ✅ Matched Skills
                matched = resume.get("matched_skills", [])
                if matched:
                    st.markdown("**✅ Matched Skills (from JD):**")
                    matched_cards = " ".join([
                        f"<span style='display:inline-block;background:#c8e6c9;color:#1b5e20;"
                        f"padding:6px 12px;margin:3px;border-radius:10px'>{s}</span>"
                        for s in matched
                    ])
                    st.markdown(matched_cards, unsafe_allow_html=True)

                # ⚠️ Missing Skills
                missing = resume.get("missing_skills", [])
                if missing:
                    st.markdown("**⚠️ Missing Skills (from JD):**")
                    missing_cards = " ".join([
                        f"<span style='display:inline-block;background:#ffcdd2;color:#b71c1c;"
                        f"padding:6px 12px;margin:3px;border-radius:10px'>{s}</span>"
                        for s in missing
                    ])
                    st.markdown(missing_cards, unsafe_allow_html=True)

                # 🟡 Other Skills
                other = resume.get("other_skills", [])
                if other:
                    st.markdown("**🟡 Other Skills (not in JD):**")
                    other_cards = " ".join([
                        f"<span style='display:inline-block;background:#fff9c4;color:#f57f17;"
                        f"padding:6px 12px;margin:3px;border-radius:10px'>{s}</span>"
                        for s in other
                    ])
                    st.markdown(other_cards, unsafe_allow_html=True)

                # 🧮 Total Experience
                exp_years = resume.get("total_experience_years", "N/A")
                st.markdown(
                    f"<span style='display:inline-block;background:#fff8e1;color:#f57f17;"
                    f"padding:8px 14px;margin:3px;border-radius:10px;font-weight:600;'>"
                    f"🧮 Total Experience: {exp_years}</span>",
                    unsafe_allow_html=True
                )

                # 🎯 Score
                score = resume.get("score", "N/A")
                st.markdown(
                    f"<span style='display:inline-block;background:#e8f5e9;color:#1b5e20;"
                    f"padding:8px 14px;margin:3px;border-radius:10px;font-weight:600;'>"
                    f"🎯 Overall Score: {score}</span>",
                    unsafe_allow_html=True
                )

                # 💬 Remarks
                remarks = resume.get("remarks", [])
                if remarks:
                    st.markdown("**💬 Remarks / Feedback:**")
                    remark_cards = " ".join([
                        f"<span style='display:inline-block;background:#fce4ec;color:#880e4f;"
                        f"padding:6px 12px;margin:3px;border-radius:10px'>{r}</span>"
                        for r in remarks
                    ])
                    st.markdown(remark_cards, unsafe_allow_html=True)

                # 📈 Scoring Breakdown
                breakdown = resume.get("scoring_breakdown", {})
                if breakdown:
                    st.markdown("**📈 Scoring Breakdown:**")
                    breakdown_cards = " ".join([
                        f"<span style='display:inline-block;background:#e3f2fd;color:#0d47a1;"
                        f"padding:6px 12px;margin:3px;border-radius:10px'>"
                        f"{k.capitalize()}: {v}</span>"
                        for k, v in breakdown.items()
                    ])
                    st.markdown(breakdown_cards, unsafe_allow_html=True)



# --------------------------
# Export Options
# --------------------------

# st.subheader("Export Options")

# st.session_state.export_option = st.radio(
#     "Choose Export Option:",
#     ("Create New Excel File", "Append to Existing Sheet", "Create New Sheet in Existing File")
# )

# # -------------------------- Create New Excel File --------------------------
# if st.session_state.export_option == "Create New Excel File":
#     st.session_state.save_mode = "new_file"
#     file_name_input = st.text_input("Enter Excel File Name", "resumes.xlsx")
#     sheet_name_input = st.text_input("Enter Sheet Name", "Sheet1")
#     if st.button("Export New Excel"):
#         # Full path for backend
#         full_file_path = os.path.join(EXPORTS_DIR, file_name_input)
#         params = {
#             "processed_resumes": st.session_state.results,
#             "mode": st.session_state.save_mode,
#             "file_path": full_file_path,
#             "sheet_name": sheet_name_input
#         }
#         response = requests.post("http://127.0.0.1:8000/export_resumes_excel", json=params)
#         if response.status_code == 200:
#             st.session_state.excel_file = response.json()
#             st.success("✅ Excel exported successfully!")

# # -------------------------- Append to Existing Sheet --------------------------
# elif st.session_state.export_option == "Append to Existing Sheet":
#     st.session_state.save_mode = "append_sheet"
#     excel_files = [f for f in os.listdir(EXPORTS_DIR) if f.endswith(".xlsx")]
#     if excel_files:
#         selected_file = st.selectbox("Select Existing Excel File", excel_files)
#         if selected_file:
#             full_file_path = os.path.join(EXPORTS_DIR, selected_file)
#             wb = openpyxl.load_workbook(full_file_path)
#             sheet_names = wb.sheetnames
#             selected_sheet = st.selectbox("Select Existing Sheet", sheet_names)
#             if st.button("Append to Sheet"):
#                 params = {
#                     "processed_resumes": st.session_state.results,
#                     "mode": st.session_state.save_mode,
#                     "file_path": full_file_path,
#                     "sheet_name": selected_sheet
#                 }
#                 response = requests.post("http://127.0.0.1:8000/export_resumes_excel", json=params)
#                 if response.status_code == 200:
#                     st.session_state.excel_file = response.json()
#                     st.success("✅ Data appended successfully!")
#     else:
#         st.warning("No existing Excel files found in exports/")

# # -------------------------- Create New Sheet in Existing File --------------------------
# elif st.session_state.export_option == "Create New Sheet in Existing File":
#     st.session_state.save_mode = "new_sheet"
#     excel_files = [f for f in os.listdir(EXPORTS_DIR) if f.endswith(".xlsx")]
#     if excel_files:
#         selected_file = st.selectbox("Select Existing Excel File", excel_files)
#         if selected_file:
#             full_file_path = os.path.join(EXPORTS_DIR, selected_file)
#             new_sheet_name = st.text_input("Enter New Sheet Name", "Sheet1")
#             if st.button("Create New Sheet"):
#                 params = {
#                     "processed_resumes": st.session_state.results,
#                     "mode": st.session_state.save_mode,
#                     "file_path": full_file_path,
#                     "sheet_name": new_sheet_name
#                 }
#                 response = requests.post("http://127.0.0.1:8000/export_resumes_excel", json=params)
#                 if response.status_code == 200:
#                     st.session_state.excel_file = response.json()
#                     st.success("✅ New sheet created successfully!")
#     else:
#         st.warning("No existing Excel files found in exports/")

# # -------------------------- Download Button --------------------------
# if st.session_state.excel_file:
#     excel_b64 = st.session_state.excel_file["excel_file"]
#     excel_bytes = base64.b64decode(excel_b64)
#     saved_path = st.session_state.excel_file["saved_path"]
#     st.download_button(
#         label="Download Excel",
#         data=excel_bytes,
#         file_name=os.path.basename(saved_path),
#         mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#     )
import os
import base64
import requests
import streamlit as st
from openpyxl import load_workbook

st.subheader("Export Options")

# Initialize session state variables if not already
if "export_option" not in st.session_state:
    st.session_state.export_option = "Create New Excel File"
if "save_mode" not in st.session_state:
    st.session_state.save_mode = "new_file"
if "excel_file" not in st.session_state:
    st.session_state.excel_file = None

# -------------------------- Export Option --------------------------
st.session_state.export_option = st.radio(
    "Choose Export Option:",
    ("Create New Excel File", "Append to Existing Sheet", "Create New Sheet in Existing File")
)

# -------------------------- Common Export Logic --------------------------
def export_to_backend(params):
    try:
        response = requests.post("http://127.0.0.1:8000/export_resumes_excel", json=params)
        if response.status_code == 200:
            resp_json = response.json()
            if resp_json.get("status") == "success" and "excel_file" in resp_json:
                st.session_state.excel_file = resp_json
                st.success("✅ Export successful!")
            else:
                st.warning(f"❌ Export failed: {resp_json.get('message', 'Unknown error')}")
        else:
            st.warning(f"❌ Backend returned status {response.status_code}")
    except Exception as e:
        st.error(f"❌ Exception during export: {str(e)}")

# -------------------------- Create New Excel File --------------------------
if st.session_state.export_option == "Create New Excel File":
    st.session_state.save_mode = "new_file"
    file_name_input = st.text_input("Enter Excel File Name", "resumes.xlsx")
    sheet_name_input = st.text_input("Enter Sheet Name", "Sheet1")
    if st.button("Export New Excel"):
        full_file_path = os.path.join(EXPORTS_DIR, file_name_input)
        params = {
            "processed_resumes": st.session_state.results,
            "mode": st.session_state.save_mode,
            "file_path": full_file_path,
            "sheet_name": sheet_name_input
        }
        export_to_backend(params)

# -------------------------- Append to Existing Sheet --------------------------
elif st.session_state.export_option == "Append to Existing Sheet":
    st.session_state.save_mode = "append_sheet"
    excel_files = [f for f in os.listdir(EXPORTS_DIR) if f.endswith(".xlsx")]
    if excel_files:
        selected_file = st.selectbox("Select Existing Excel File", excel_files)
        if selected_file:
            full_file_path = os.path.join(EXPORTS_DIR, selected_file)
            wb = load_workbook(full_file_path)
            selected_sheet = st.selectbox("Select Existing Sheet", wb.sheetnames)
            if st.button("Append to Sheet"):
                params = {
                    "processed_resumes": st.session_state.results,
                    "mode": st.session_state.save_mode,
                    "file_path": full_file_path,
                    "sheet_name": selected_sheet
                }
                export_to_backend(params)
    else:
        st.warning("No existing Excel files found in exports/")

# -------------------------- Create New Sheet in Existing File --------------------------
elif st.session_state.export_option == "Create New Sheet in Existing File":
    st.session_state.save_mode = "new_sheet"
    excel_files = [f for f in os.listdir(EXPORTS_DIR) if f.endswith(".xlsx")]
    if excel_files:
        selected_file = st.selectbox("Select Existing Excel File", excel_files)
        if selected_file:
            full_file_path = os.path.join(EXPORTS_DIR, selected_file)
            new_sheet_name = st.text_input("Enter New Sheet Name", "Sheet1")
            if st.button("Create New Sheet"):
                params = {
                    "processed_resumes": st.session_state.results,
                    "mode": st.session_state.save_mode,
                    "file_path": full_file_path,
                    "sheet_name": new_sheet_name
                }
                export_to_backend(params)
    else:
        st.warning("No existing Excel files found in exports/")

# -------------------------- Download Button --------------------------
if st.session_state.get("excel_file") and st.session_state.excel_file.get("excel_file"):
    excel_b64 = st.session_state.excel_file["excel_file"]
    excel_bytes = base64.b64decode(excel_b64)
    saved_path = st.session_state.excel_file.get("saved_path", "resumes.xlsx")
    st.download_button(
        label="Download Excel",
        data=excel_bytes,
        file_name=os.path.basename(saved_path),
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
