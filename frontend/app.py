import streamlit as st
import requests
import base64
import os
import pandas as pd

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
    st.session_state.save_mode = "new"

if "results" not in st.session_state:
    st.session_state.results = None

if "excel_file" not in st.session_state:
    st.session_state.excel_file = None

# --------------------------
# Title
# --------------------------
st.title("Resume Scanner System")

# --------------------------
# Step 1: Upload Files
# --------------------------
if st.session_state.step == 1:
    st.header("Step 1: Upload Resume Files")
    uploaded_files = st.file_uploader("Upload resumes (PDF/DOCX)", type=["pdf","docx"], accept_multiple_files=True)
    
    if uploaded_files:
        st.session_state.uploaded_files = uploaded_files
        if st.button("Upload Resume(s)"):
            # Upload resumes to backend
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

    # Example editable JD template (kept as requested)
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

    # --------------------------
    # Weights sliders
    # --------------------------
    st.subheader("Weights (adjust using sliders)")
    st.session_state.weights["skills"] = st.slider("Skills Weight", 0.0, 1.0, st.session_state.weights["skills"], 0.05)
    st.session_state.weights["experience"] = st.slider("Experience Weight", 0.0, 1.0, st.session_state.weights["experience"], 0.05)
    st.session_state.weights["education"] = st.slider("Education Weight", 0.0, 1.0, st.session_state.weights["education"], 0.05)
    st.session_state.weights["certifications"] = st.slider("Certifications Weight", 0.0, 1.0, st.session_state.weights["certifications"], 0.05)

    # --------------------------
    # Save mode
    # --------------------------
    st.subheader("Save Mode")
    st.session_state.save_mode = st.radio("Choose save mode for Excel", ["new", "append"], index=0)

    # --------------------------
    # Next button to send JD + weights
    # --------------------------
    if st.button("Evaluate Resume(s)"):
        if not st.session_state.uploaded_paths or not jd_text.strip():
            st.warning("Please upload resumes and enter JD before proceeding.")
        else:
            # Upload JD + weights to backend
            params = {
                "jd_text": jd_text,
                "skills_weight": st.session_state.weights["skills"],
                "experience_weight": st.session_state.weights["experience"],
                "education_weight": st.session_state.weights["education"],
                "certifications_weight": st.session_state.weights["certifications"],
                "save_mode": st.session_state.save_mode
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

    with st.spinner("Evaluating resumes, please wait..."):
        response = requests.post(
            "http://127.0.0.1:8000/evaluate_resumes",
            json={
                "uploaded_paths": st.session_state.uploaded_paths,
                "jd_data": st.session_state.jd_data
            }
        )

    if response.status_code == 200:
        st.session_state.results = response.json()["data"]
        st.success("✅ Evaluation completed!")
        st.session_state.step = 4
    else:
        st.error(f"Evaluation failed: {response.text}")

# ------------------ Step 4: Display Results ------------------
if st.session_state.step >= 4 and st.session_state.results:
    st.subheader("Step 4: Evaluation Results")

    for resume in st.session_state.results:
        name = resume.get("name", "Unnamed Candidate")
        with st.expander(f"▶ {name}"):
            # Basic info
            st.markdown(f"**Email:** {resume.get('email','')}")
            st.markdown(f"**Phone:** {resume.get('phone','')}")

            # URLs
            urls = resume.get("urls", [])
            if isinstance(urls, list) and urls:
                st.markdown("**URLs:**")
                for url in urls:
                    st.markdown(f"- {url}")

            # Skills
            skills = resume.get("skills", [])
            if isinstance(skills, list) and skills:
                st.markdown("**Skills:**")
                skill_cards = " ".join([f"<span style='display:inline-block;background:#e0f7fa;color:#006064;padding:5px 10px;margin:3px;border-radius:8px'>{s}</span>" for s in skills])
                st.markdown(skill_cards, unsafe_allow_html=True)

            # Education
            education = resume.get("education", [])
            if isinstance(education, list) and education:
                st.markdown("**Education:**")
                edu_cards = " ".join([f"<span style='display:inline-block;background:#f1f8e9;color:#33691e;padding:5px 10px;margin:3px;border-radius:8px'>{edu.get('degree','')} - {edu.get('institution','')} ({edu.get('year','')})</span>" for edu in education if isinstance(edu, dict)])
                st.markdown(edu_cards, unsafe_allow_html=True)

            # Experience
            experience = resume.get("experience", [])
            if isinstance(experience, list) and experience:
                st.markdown("**Experience:**")
                exp_cards = " ".join([f"<span style='display:inline-block;background:#fff3e0;color:#e65100;padding:5px 10px;margin:3px;border-radius:8px'>{exp.get('role','')} at {exp.get('company','')} ({exp.get('start_date','')} - {exp.get('end_date','')})</span>" for exp in experience if isinstance(exp, dict)])
                st.markdown(exp_cards, unsafe_allow_html=True)

            # Projects
            projects = resume.get("projects", [])
            if isinstance(projects, list) and projects:
                st.markdown("**Projects:**")
                proj_cards = " ".join([f"<span style='display:inline-block;background:#f3e5f5;color:#4a148c;padding:5px 10px;margin:3px;border-radius:8px'>{proj.get('title','')} [{', '.join(proj.get('technologies',[]))}]: {proj.get('description','')}</span>" for proj in projects if isinstance(proj, dict)])
                st.markdown(proj_cards, unsafe_allow_html=True)

            # Certifications
            certs = resume.get("certifications", [])
            if isinstance(certs, list) and certs:
                st.markdown("**Certifications:**")
                cert_cards = " ".join([f"<span style='display:inline-block;background:#ede7f6;color:#311b92;padding:5px 10px;margin:3px;border-radius:8px'>{c}</span>" for c in certs])
                st.markdown(cert_cards, unsafe_allow_html=True)

            # Experience Years, Score, Remarks
            st.markdown("**Experience Years:**")
            st.markdown(f"<span style='display:inline-block;background:#c8e6c9;color:#1b5e20;padding:5px 10px;margin:3px;border-radius:8px'>{resume.get('total_experience',0)}</span>", unsafe_allow_html=True)

            st.markdown("**Score:**")
            score_color = "#c8e6c9" if resume.get("score",0) >= 70 else "#fff9c4" if resume.get("score",0) >= 50 else "#ffcdd2"
            st.markdown(f"<span style='display:inline-block;background:{score_color};color:#000;padding:5px 10px;margin:3px;border-radius:8px'>{resume.get('score','')}</span>", unsafe_allow_html=True)

            remarks = resume.get("remarks", [])
            if isinstance(remarks, list) and remarks:
                st.markdown("**Remarks:**")
                remark_cards = " ".join([f"<span style='display:inline-block;background:#ffe0b2;color:#bf360c;padding:5px 10px;margin:3px;border-radius:8px'>{r}</span>" for r in remarks])
                st.markdown(remark_cards, unsafe_allow_html=True)

    # -------------------------- Download Excel --------------------------
    if st.session_state.excel_file is None:
        if st.button("Export & Download Excel"):
            with st.spinner("Exporting Excel... ⏳"):
                response = requests.post(
                    "http://127.0.0.1:8000/export_resumes_excel",
                    json={
                        "processed_resumes": st.session_state.results,
                        "save_mode": st.session_state.save_mode
                    }
                )
            if response.status_code == 200:
                st.success("✅ Excel exported successfully!")
                st.session_state.excel_file = response.json()
            else:
                st.error(f"Failed to export Excel: {response.text}")

    if st.session_state.excel_file:
        excel_b64 = st.session_state.excel_file["excel_file"]
        excel_bytes = base64.b64decode(excel_b64)
        file_name = os.path.basename(st.session_state.excel_file["saved_path"])
        st.download_button(
            label="Download Excel Now",
            data=excel_bytes,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )