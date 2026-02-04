
from logging import PlaceHolder
import os
import base64
import requests
import streamlit as st
import re
import pymongo
from utils import force_rerun, safe_rerun

# def reset_fetch_state():
#     keys_to_clear = [
#         "fetch_step",
#         "fetch_jd_text",
#         "fetch_weights",
#         "fetch_evaluation_done",
#         "fetch_evaluation_response",
#         "fetch_results",
#         "fetch_excel_file",
#         "fetch_jd_data",
#         "fetch_save_mode",
#         "fetch_export_option",
#         "fetch_resume_count",
#         "fetch_jd_fields",
#         "fetch_jd_json"
#     ]
#     for k in keys_to_clear:
#         st.session_state.pop(k, None)
def reset_fetch_state():
    st.session_state.fetch_step = 1
    st.session_state.fetch_jd_text = ""
    st.session_state.fetch_weights = {
        "skills": 0.4,
        "experience": 0.3,
        "education": 0.2,
        "certifications": 0.1
    }
    st.session_state.fetch_evaluation_done = False
    st.session_state.fetch_evaluation_response = None
    st.session_state.fetch_results = None
    st.session_state.fetch_excel_file = None
    st.session_state.fetch_jd_data = None
    st.session_state.fetch_save_mode = None
    st.session_state.fetch_export_option = None
    st.session_state.fetch_resume_count = 0
    st.session_state.fetch_jd_fields = []
    st.session_state.fetch_jd_json = {}
    st.session_state.fetch_page = 1
    st.session_state.mongo_url = ""
    st.session_state.db_name = ""
    st.session_state.collection_name = ""



def app():
        st.set_page_config(
            page_title="Resume Evaluator",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # --------------------------
        # Session & Auth Handling
        # --------------------------
        if "auth_token" not in st.session_state:
            st.session_state.auth_token = None
        if "current_user" not in st.session_state:
            st.session_state.current_user = None


        # --------------------------
        # Session State Defaults
        # --------------------------
        if "fetch_step" not in st.session_state:
            st.session_state.fetch_step = 1
        if "fetch_jd_text" not in st.session_state:
            st.session_state.fetch_jd_text = ""
        if "fetch_weights" not in st.session_state:
            st.session_state.fetch_weights = {
                "skills": 0.4,
                "experience": 0.3,
                "education": 0.2,
                "certifications": 0.1
            }
        if "fetch_resume_count" not in st.session_state:
            st.session_state.fetch_resume_count = 0
        if "fetch_evaluation_done" not in st.session_state:
            st.session_state.fetch_evaluation_done = False
        if "fetch_evaluation_response" not in st.session_state:
            st.session_state.fetch_evaluation_response = None
        if "fetch_results" not in st.session_state:
            st.session_state.fetch_results = None
        if "fetch_excel_file" not in st.session_state:
            st.session_state.fetch_excel_file = None
        if "fetch_jd_data" not in st.session_state:
            st.session_state.fetch_jd_data = None
        if "fetch_jd_fields" not in st.session_state:
            st.session_state.fetch_jd_fields = []
        if "fetch_jd_json" not in st.session_state:
            st.session_state.fetch_jd_json = {}
        if "current_user" not in st.session_state:
            st.session_state.current_user = None
        if "llm_model" not in st.session_state:
            # default model (can be overridden by sidebar)
            st.session_state.llm_model = "gemini-2.5-flash"
        if "llm_api_key" not in st.session_state:
            st.session_state.llm_api_key = None
        if "fetch_save_mode" not in st.session_state:
            st.session_state.fetch_save_mode = None
        if "show_auth" not in st.session_state:
            # When True, the sidebar shows the login/register form. Clear after login.
            st.session_state.show_auth = True
        if "fetch_resume_count" not in st.session_state:      
            st.session_state.fetch_resume_count = 0
        if "mongo_url" not in st.session_state:
            st.session_state.mongo_url = ""
        if "db_name" not in st.session_state:
            st.session_state.db_name = ""
        if "collection_name" not in st.session_state:
            st.session_state.collection_name = ""


        # Fetch username after login if token exists but username missing
        if not st.session_state.current_user and st.session_state.get("auth_token"):
            try:
                headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
                resp = requests.get("http://127.0.0.1:8000/me", headers=headers)
                if resp.status_code == 200:
                    st.session_state.current_user = resp.json().get("username")
                else:
                    st.warning("⚠️ Failed to fetch user info. Please re-login.")
            except Exception as e:
                st.error(f"Exception fetching user info: {e}")
                


        username = st.session_state.get("current_user") or "Guest"
        top_col1, top_col2 = st.columns([8, 1])
        with top_col1:
            st.subheader(f"👋 Welcome, {username}!")
        with top_col2:
            if st.button("🔄", help="Refresh app"):
                reset_fetch_state()
                force_rerun()


        # --------------------------
        # Sidebar: Account + LLM Settings
        # --------------------------
        def logout():
                st.session_state.auth_token = None
                st.session_state.current_user = None
                st.session_state.show_auth = True
                st.session_state.user_role = None           # clear role if you track it
                st.session_state.selected_app = None        # reset selected app card   
                reset_fetch_state()             
                force_rerun()
        with st.sidebar:
            # -------------------------
            # Account
            # -------------------------
            st.header("Account")
            st.markdown(f"**Signed in as:** {st.session_state.current_user}")

            st.button("Logout", key="btn_logout",on_click=logout)

            st.markdown("---")

            # -------------------------
            # LLM Settings (optional)
            # -------------------------
            st.subheader("LLM Settings (optional)")

            model_choices = {
                "Gemini 2.5 Flash (fast, recommended)": "gemini-2.5-flash",
                "Gemini 2.5 Flash Lite (higher rpd)": "gemini-2.5-flash-lite",
                "Gemini 1.5 Pro (balanced)": "gemini-1.5-pro",
                "Gemini 1.0 (smaller, cheaper)": "gemini-1.0",
                "Custom model name": "custom",
            }

            model_label = st.selectbox(
                "Choose model",
                list(model_choices.keys()),
                index=0,
                key="_llm_model_select",
            )

            selected_model_value = model_choices[model_label]

            if selected_model_value == "custom":
                custom_model = st.text_input(
                    "Custom model name",
                    key="_llm_model_custom",
                )
                model_value = custom_model or "gemini-2.5-flash"
            else:
                model_value = selected_model_value

            api_key_input = st.text_input(
                "Model API Key (optional)",
                type="password",
                key="_llm_api_key",
            )

            # Persist settings (UNCHANGED)
            if model_value:
                st.session_state.llm_model = model_value
            if api_key_input:
                st.session_state.llm_api_key = api_key_input


        # --------------------------
        # Step 1: MongoDB Credentials
        # --------------------------

        if st.session_state.fetch_step >= 1:
            st.header("Step 1: Enter MongoDB Details to Fetch Resumes")

            st.markdown(
                """
                Provide MongoDB connection details to fetch resumes (already parsed JSONs).
                """
            )

            mongo_url = st.text_input(
                "MongoDB URL",
                value=st.session_state.get(
                    "mongo_url",
                    ""
                    
                ),placeholder="Enter MongoDB Atlas Connection URL"
            )

            col1, col2 = st.columns(2)

            with col1:
                db_name = st.text_input(
                    "Database Name", value=st.session_state.get("db_name", ""), placeholder="Enter Databse Name"
                )
            with col2:
                collection_name = st.text_input(
                    "Collection Name", value=st.session_state.get("collection_name", ""),placeholder="Enter Collection Name"
                )

        
            if st.button("Connect & Continue"):
                # --- BASIC VALIDATION ---
                if not mongo_url or not db_name or not collection_name:
                    st.warning("All fields are required.")
                    st.stop()

                if not st.session_state.get("auth_token"):
                    st.warning("Please login before connecting to MongoDB.")
                    st.stop()

                # --- SPINNER ---
                with st.spinner("Connecting to MongoDB..."):
                    try:
                        headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
                        payload = {
                            "mongo_url": mongo_url,
                            "db_name": db_name,
                            "collection_name": collection_name,
                        }

                        resp = requests.post(
                            "http://127.0.0.1:8000/db/connect_mongo",
                            json=payload,
                            headers=headers,
                            timeout=25,
                        )

                        try:
                            data = resp.json()
                        except ValueError:
                            st.error("Server returned an invalid response.")
                            # ❌ DO NOT STOP HERE INSIDE SPINNER
                            pass

                    except requests.exceptions.Timeout:
                        st.error("Server is taking too long to respond.")
                        pass
                    except requests.exceptions.ConnectionError:
                        st.error("Cannot reach backend API.")
                        pass
                    except Exception:
                        st.error("Unexpected error occurred.")
                        pass

                # SUCCESS
                if resp.status_code == 200:
                    st.session_state.fetch_resume_count = data.get("resume_count", 0)
                    st.session_state.mongo_url = mongo_url
                    st.session_state.db_name = db_name
                    st.session_state.collection_name = collection_name
                    st.session_state.fetch_step = 2

                    st.success(f"Connected! Resumes found: {st.session_state.fetch_resume_count}")
                    safe_rerun()

                # AUTH ERROR
                elif resp.status_code == 401:
                    st.session_state.auth_token = None
                    st.session_state.fetch_step = 0
                    st.error(data.get("message", "Session expired. Please login again."))
                    st.stop()

                # OTHER BACKEND ERRORS
                else:
                    st.error(data.get("message", "Unable to connect to MongoDB."))
                    st.stop()
    # ---------------------------
    # Step 2: JD Upload
    # ---------------------------
        if st.session_state.fetch_step >= 2:
            st.header("Step 2: Upload Job Description & Assign Weights")

            jd_file = st.file_uploader(
                "📄 Upload Job Description (PDF/DOCX)",
                type=["pdf", "docx"],
                key="fetch_jd_file"
            )

            upload_clicked = False
            if jd_file:
                upload_clicked = st.button("Upload JD")

            if upload_clicked:
                headers = {}
                if st.session_state.auth_token:
                    headers["Authorization"] = f"Bearer {st.session_state.auth_token}"
                if st.session_state.llm_model:
                    headers["X-Model"] = st.session_state.llm_model
                if st.session_state.llm_api_key:
                    headers["X-Api-Key"] = st.session_state.llm_api_key

                files = {
                    "file": (jd_file.name, jd_file, jd_file.type)
                }

                with st.spinner("⏳ Processing JD and generating sliders..."):
                    response = requests.post(
                        "http://127.0.0.1:8000/upload_jd",
                        headers=headers,
                        files=files
                    )

                if response.status_code == 200:
                    data = response.json()
                    st.session_state.fetch_jd_fields = data.get("jd_fields", [])
                    st.session_state.fetch_jd_json = data.get("jd_json", {})
                    st.success("✅ JD processed successfully! Sliders generated.")
                else:
                    st.error(f"❌ JD upload failed: {response.text}")
                    st.stop()

            # 🚫 Block if JD not uploaded
            if not st.session_state.fetch_jd_fields:
                st.warning("⚠️ Please upload a valid Job Description file to proceed.")
                st.stop()

            # 🎚️ Sliders
            st.subheader("🎚️ Assign Weights")
            st.caption(
                "You can assign any weight values. Even if the total exceeds 100, "
                "the system automatically normalizes weights during scoring, "
                "so the final candidate score will always be out of 100."
            )
            weights = {}
            for field in st.session_state.fetch_jd_fields:
                default_val = st.session_state.fetch_weights.get(field, 0.2) * 100
                weights[field] = st.slider(
                    f"{field.capitalize()} Weight (%)",
                    0, 100, int(default_val), 5,
                    key=f"fetch_w_{field}"   
                )

            total = sum(weights.values())
            st.markdown(f"**Total Weight Sum:** `{total}`")

            st.session_state.fetch_weights = {
                k: round(v / 100, 2) for k, v in weights.items()
            }

            if st.button("Proceed to Evaluation", key="fetch_btn_proceed"):
                if st.session_state.fetch_resume_count == 0:
                    st.warning("No resumes found in DB.")
                    st.stop()

                st.session_state.fetch_jd_data = {
                    "jd_json": st.session_state.fetch_jd_json,
                    "weights": st.session_state.fetch_weights
                }

                st.session_state.fetch_step = 3




        # --------------------------
        # Step 3: Evaluate Resumes (from DB)
        # --------------------------
        if st.session_state.fetch_step >= 3:
            st.header("Step 3: Evaluating Resumes from MongoDB...")

            if not st.session_state.fetch_evaluation_done:
                with st.spinner("⏳ Evaluating resumes... This may take a few minutes."):
                    headers = {}
                    if st.session_state.auth_token:
                        headers["Authorization"] = f"Bearer {st.session_state.auth_token}"
                    if st.session_state.get("llm_model"):
                        headers["X-Model"] = st.session_state.get("llm_model")
                    if st.session_state.get("llm_api_key"):
                        headers["X-Api-Key"] = st.session_state.get("llm_api_key")

                    payload = {
                        "mongo_url": st.session_state.mongo_url,
                        "db_name": st.session_state.db_name,
                        "collection_name": st.session_state.collection_name,
                        "jd_data": st.session_state.fetch_jd_data  # may be None
                    }

                    try:
                        response = requests.post(
                            "http://127.0.0.1:8000/db/evaluate_resumes_db",
                            json=payload,
                            headers=headers
                        )
                        st.session_state.fetch_evaluation_response = response
                        st.session_state.fetch_evaluation_done = True
                    except Exception as e:
                        st.error(f"⚠️ Request failed: {e}")
                        st.stop()

            # Process response
            response = st.session_state.fetch_evaluation_response
            if response.status_code == 200:
                result_json = response.json()
                st.session_state.fetch_results = result_json.get("data", [])
                jd_mode = result_json.get("jd_mode", "disabled")

                if jd_mode == "enabled":
                    st.success("✅ Evaluation completed with JD scoring!")
                else:
                    st.success("✅ Resume parsing completed (no JD provided).")

                st.session_state.fetch_step = 4
            else:
                st.error(f"❌ Evaluation failed: {response.text}")



        # --------------------------
        # Step 4: Display Results
        # --------------------------

        # if st.session_state.fetch_step >= 4 and st.session_state.fetch_results:
        #     st.subheader("Review Evaluation Results")
        #     sorted_results = sorted(
        #         st.session_state.fetch_results,
        #         key=lambda r: r.get("evaluations", [{}])[-1].get("score", 0),
        #         reverse=True
        #     )
        #     for resume in sorted_results:
        #         resume_json = resume.get("resume_json", {})
        #         evaluations = resume.get("evaluations", [])
        #         latest_eval = evaluations[-1] if evaluations else {}

        #         name = resume_json.get("name", "Unnamed Candidate").title()
        #         score=latest_eval.get("score","N/A")
        #         email=resume_json.get("email","")
        #         contact=resume_json.get("phone","")
        #         with st.expander(f"▶ {name} | Score: {score} | Email: {email} | Contact: {contact}"):
        if st.session_state.fetch_step >= 4 and st.session_state.fetch_results:
            st.subheader("Review Evaluation Results")

            ITEMS_PER_PAGE = 10

            if "fetch_page" not in st.session_state:
                st.session_state.fetch_page = 1

            def get_latest_score(resume):
                evaluations = resume.get("evaluations", [])
                if evaluations:
                    return evaluations[-1].get("score", 0)
                return 0

            sorted_results = sorted(
                st.session_state.fetch_results,
                key=get_latest_score,
                reverse=True
            )
            evaluated_count = len(sorted_results)

            st.markdown(
                f"""
                <div style="
                    background:#1e293b;
                    color:#e5e7eb;
                    border-left:4px solid #60a5fa;
                    padding:10px 14px;
                    border-left:4px solid #1976d2;
                    border-radius:6px;
                    margin-bottom:12px;
                    font-size:14px;
                ">
                    ℹ️ <b>Showing {evaluated_count} evaluated resumes</b><br>
                    Resumes with no matching JD skills were filtered out and not evaluated.
                </div>
                """,
                unsafe_allow_html=True
            )

            total_items = len(sorted_results)
            total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

            start_idx = (st.session_state.fetch_page - 1) * ITEMS_PER_PAGE
            end_idx = start_idx + ITEMS_PER_PAGE
            page_results = sorted_results[start_idx:end_idx]
            

            for resume in page_results:
                resume_json = resume.get("resume_json", {})
                evaluations = resume.get("evaluations", [])
                latest_eval = evaluations[-1] if evaluations else {}

                name = resume_json.get("name", "Unnamed Candidate").title()
                score = latest_eval.get("score", "N/A")
                email = resume_json.get("email", "")
                contact = resume_json.get("phone", "")

                with st.expander(f"▶ {name}   | Score: {score}   | Email: {email}   | Contact: {contact}"):

                    st.markdown(f"**Email:** {resume_json.get('email','')}")
                    st.markdown(f"**Phone:** {resume_json.get('phone','')}")
                    st.markdown(f"**Location:** {resume_json.get('location','')}")
                    # URLs
                    urls = resume_json.get("urls", [])
                    if urls:
                        st.markdown("**URLs:**")
                        for url in urls:
                            st.markdown(f"- {url}")

                    # Skills
                    skills = resume_json.get("skills", [])
                    if skills:
                        st.markdown("**Skills:**")
                        skill_cards = " ".join([
                            f"<span style='display:inline-block;background:#e0f7fa;color:#006064;"
                            f"padding:5px 10px;margin:3px;border-radius:8px'>{s}</span>"
                            for s in skills
                        ])
                        st.markdown(skill_cards, unsafe_allow_html=True)

                    # Education
                    education = resume_json.get("education", [])
                    if education:
                        st.markdown("**Education:**")
                        edu_cards = " ".join([
                            f"<span style='display:inline-block;background:#f1f8e9;color:#33691e;"
                            f"padding:5px 10px;margin:3px;border-radius:8px'>"
                            f"{edu.get('degree','')} - {edu.get('institution','')} ({edu.get('year','')})</span>"
                            for edu in education if isinstance(edu, dict)
                        ])
                        st.markdown(edu_cards, unsafe_allow_html=True)

                    # Experience
                    experience = resume_json.get("experience", [])
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

                    # Projects
                    projects = resume_json.get("projects", [])
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

                    # Certifications
                    certs = resume_json.get("certifications", [])
                    if certs:
                        st.markdown("**Certifications:**")
                        cert_cards = " ".join([
                            f"<span style='display:inline-block;background:#ede7f6;color:#311b92;"
                            f"padding:5px 10px;margin:3px;border-radius:8px'>{c}</span>"
                            for c in certs
                        ])
                        st.markdown(cert_cards, unsafe_allow_html=True)

                    # --------------------------
                    # Summary Section
                    # --------------------------
                    st.markdown("---")
                    st.markdown("### 📊 Summary")

                    # Matched Skills
                    matched = latest_eval.get("matched_skills", [])
                    if matched:
                        st.markdown("**✅ Matched Skills (from JD):**")
                        matched_cards = " ".join([
                            f"<span style='display:inline-block;background:#c8e6c9;color:#1b5e20;"
                            f"padding:6px 12px;margin:3px;border-radius:10px'>{s}</span>"
                            for s in matched
                        ])
                        st.markdown(matched_cards, unsafe_allow_html=True)

                    # Missing Skills
                    missing = latest_eval.get("missing_skills", [])
                    if missing:
                        st.markdown("**⚠️ Missing Skills (from JD):**")
                        missing_cards = " ".join([
                            f"<span style='display:inline-block;background:#ffcdd2;color:#b71c1c;"
                            f"padding:6px 12px;margin:3px;border-radius:10px'>{s}</span>"
                            for s in missing
                        ])
                        st.markdown(missing_cards, unsafe_allow_html=True)

                    # Other Skills
                    other = latest_eval.get("other_skills", [])
                    if other:
                        st.markdown("**🟡 Other Skills (not in JD):**")
                        other_cards = " ".join([
                            f"<span style='display:inline-block;background:#fff9c4;color:#f57f17;"
                            f"padding:6px 12px;margin:3px;border-radius:10px'>{s}</span>"
                            for s in other
                        ])
                        st.markdown(other_cards, unsafe_allow_html=True)

                    # Total Experience
                    exp_years = resume_json.get("total_experience_years", "N/A")
                    st.markdown(
                        f"<span style='display:inline-block;background:#fff8e1;color:#f57f17;"
                        f"padding:8px 14px;margin:3px;border-radius:10px;font-weight:600;'>"
                        f"🧮 Total Experience: {exp_years}</span>",
                        unsafe_allow_html=True
                    )

                    # Overall Score
                    score = latest_eval.get("score", "N/A")
                    st.markdown(
                        f"<span style='display:inline-block;background:#e8f5e9;color:#1b5e20;"
                        f"padding:8px 14px;margin:3px;border-radius:10px;font-weight:600;'>"
                        f"🎯 Overall Score: {score}</span>",
                        unsafe_allow_html=True
                    )

                    # Remarks
                    remarks = latest_eval.get("overall_summary", [])
                    if remarks:
                        st.markdown("**💬 Remarks / Feedback:**")
                        remark_cards = " ".join([
                            f"<span style='display:inline-block;background:#fce4ec;color:#880e4f;"
                            f"padding:6px 12px;margin:3px;border-radius:10px'>{r}</span>"
                            for r in remarks
                        ])
                        st.markdown(remark_cards, unsafe_allow_html=True)

                    # Scoring Breakdown
                    breakdown = latest_eval.get("scoring_breakdown", {})
                    if breakdown:
                        st.markdown("**📈 Scoring Breakdown:**")
                        breakdown_cards = " ".join([
                            f"<span style='display:inline-block;background:#e3f2fd;color:#0d47a1;"
                            f"padding:6px 12px;margin:3px;border-radius:10px'>{k.capitalize()}: {v}</span>"
                            for k, v in breakdown.items()
                        ])
                        st.markdown(breakdown_cards, unsafe_allow_html=True)
            # Pagination controls
            col1, col2, col3 = st.columns([1, 2, 1])

            with col1:
                if st.button("⬅ Prev", key="fetch_prev", disabled=st.session_state.fetch_page <= 1):
                    st.session_state.fetch_page -= 1
                    st.rerun()

            with col2:
                st.markdown(
                    f"<div style='text-align:center;font-weight:600;'>"
                    f"Page {st.session_state.fetch_page} of {total_pages}"
                    f"</div>",
                    unsafe_allow_html=True
                )

            with col3:
                if st.button("Next ➡", key="fetch_next", disabled=st.session_state.fetch_page >= total_pages):
                    st.session_state.fetch_page += 1
                    st.rerun()




# --------------------------------
# Export Section
# -----------------------------

        def fetch_user_export_files():
            try:
                headers = {}
                if st.session_state.get("auth_token"):
                    headers["Authorization"] = f"Bearer {st.session_state.auth_token}"
                response = requests.get("http://127.0.0.1:8000/list_exports", headers=headers)
                if response.status_code == 200:
                    return response.json().get("files", [])
                else:
                    st.warning(f"Failed to fetch export files: {response.status_code}")
                    return []
            except Exception as e:
                st.error(f"Exception fetching export files: {e}")
                return []

        def fetch_sheets_for_file(file_name):
            try:
                headers = {}
                if st.session_state.get("auth_token"):
                    headers["Authorization"] = f"Bearer {st.session_state.auth_token}"
                params = {"file_name": file_name}
                response = requests.get("http://127.0.0.1:8000/list_sheets", headers=headers, params=params)
                if response.status_code == 200:
                    return response.json().get("sheets", [])
                else:
                    st.warning(f"Failed to fetch sheets: {response.status_code}")
                    return []
            except Exception as e:
                st.error(f"Exception fetching sheets: {e}")
                return []

        # if st.session_state.get("fetch_step", 0) >= 4 and st.session_state.get("fetch_results"):
        #     st.subheader("Download Evaluation Results")
        if st.session_state.get("fetch_results"):
            st.subheader("Download Evaluation Results")
            # --- default selection
            if "fetch_export_option" not in st.session_state:
                st.session_state.fetch_export_option = "Create New Excel File"

            # --- option radio
            st.session_state.fetch_export_option = st.radio(
                "Choose Export Option:",
                (
                    "Create New Excel File",
                    "Append to Existing Sheet",
                    "Create New Sheet in Existing File",
                    "Export to MongoDB Database",
                ),
            )

            # --------------------------
            # Utility to call backend
            # --------------------------
            def export_to_backend(params):
                try:
                    headers = {}
                    if st.session_state.get("auth_token"):
                        headers["Authorization"] = f"Bearer {st.session_state.auth_token}"
                    if st.session_state.get("llm_model"):
                        headers["X-Model"] = st.session_state.llm_model
                    if st.session_state.get("llm_api_key"):
                        headers["X-Api-Key"] = st.session_state.llm_api_key

                    response = requests.post(
                        "http://127.0.0.1:8000/export_resumes_excel",
                        json=params,
                        headers=headers,
                        timeout=120
                    )

                    if response.status_code == 200:
                        resp_json = response.json()
                        if resp_json.get("status") == "success" and resp_json.get("excel_file"):
                            st.session_state.fetch_excel_file = resp_json
                            st.success("✅ Export successful!")
                        else:
                            st.warning(f"❌ Export failed: {resp_json.get('message', 'Unknown error')}")
                    else:
                        st.warning(f"❌ Backend returned status {response.status_code}")

                except Exception as e:
                    st.error(f"❌ Exception during export: {e}")

            # --------------------------
            # 1️⃣  Create New Excel File
            # --------------------------
            if st.session_state.fetch_export_option == "Create New Excel File":
                st.session_state.fetch_save_mode = "new_file"
                file_name = st.text_input("Enter Excel File Name", "resumes.xlsx")
                sheet_name = st.text_input("Enter Sheet Name", "Sheet1")

                if st.button("Export New Excel", key="btn_export_new"):
                    params = {
                        "processed_resumes": st.session_state.fetch_results,
                        "mode": "new_file",
                        "file_path": file_name,
                        "sheet_name": sheet_name,
                    }
                    export_to_backend(params)

            # --------------------------
            # 2️⃣  Append to Existing Sheet
            # --------------------------
            elif st.session_state.fetch_export_option == "Append to Existing Sheet":
                st.session_state.fetch_save_mode = "append_sheet"

                excel_files = fetch_user_export_files()

                if excel_files:
                    selected_file = st.selectbox("Select Existing Excel File", excel_files)
                    if selected_file:
                        sheets = fetch_sheets_for_file(selected_file)
                        if sheets:
                            selected_sheet = st.selectbox("Select Existing Sheet", sheets)
                        else:
                            st.warning("No sheets found in the selected file.")
                            selected_sheet = None

                        if selected_sheet and st.button("Append to Sheet", key="btn_append_sheet"):
                            params = {
                                "processed_resumes": st.session_state.fetch_results,
                                "mode": "append_sheet",
                                "file_path": selected_file,  # filename only, backend will add user folder
                                "sheet_name": selected_sheet,
                            }
                            export_to_backend(params)
                else:
                    st.warning("No existing Excel files found in your exports folder.")

            # --------------------------
            # 3️⃣  Create New Sheet in Existing File
            # --------------------------
            elif st.session_state.fetch_export_option == "Create New Sheet in Existing File":
                st.session_state.fetch_save_mode = "new_sheet"

                excel_files = fetch_user_export_files()

                if excel_files:
                    selected_file = st.selectbox("Select Existing Excel File", excel_files)
                    if selected_file:
                        new_sheet = st.text_input("Enter New Sheet Name", "Sheet1")

                        if new_sheet and st.button("Create New Sheet", key="btn_create_sheet"):
                            params = {
                                "processed_resumes": st.session_state.fetch_results,
                                "mode": "new_sheet",
                                "file_path": selected_file,  # filename only
                                "sheet_name": new_sheet,
                            }
                            export_to_backend(params)
                else:
                    st.warning("No existing Excel files found in your exports folder.")

            # --------------------------
            # 4️⃣  Export to MongoDB
            # --------------------------
            elif st.session_state.fetch_export_option == "Export to MongoDB Database":
                st.session_state.fetch_save_mode = "mongo"
                mongo_url = st.text_input("MongoDB Connection URL", "")
                db_name = st.text_input("Database Name", "resume_db")
                collection_name = st.text_input("Collection Name", "resumes")

                if st.button("Export to MongoDB", key="btn_export_mongo"):
                    if not mongo_url:
                        st.error("Please enter a valid MongoDB URL.")
                    else:
                        params = {
                            "processed_resumes": st.session_state.fetch_results,
                            "mongo_url": mongo_url,
                            "db_name": db_name,
                            "collection_name": collection_name,
                        }

                        headers = {}
                        if st.session_state.get("auth_token"):
                            headers["Authorization"] = f"Bearer {st.session_state.auth_token}"

                        with st.spinner("⏳ Uploading resumes to MongoDB..."):
                            try:
                                response = requests.post(
                                    "http://127.0.0.1:8000/export_resumes_mongo",
                                    json=params,
                                    headers=headers,
                                    timeout=120,
                                )
                                resp_json = response.json()
                                if resp_json.get("status") == "success":
                                    st.success(f"✅ Exported {resp_json.get('inserted_count')} resumes to MongoDB.")
                                else:
                                    st.warning(f"❌ Export failed: {resp_json.get('message', 'Unknown error')}")
                            except Exception as e:
                                st.error(f"❌ Exception during export: {e}")

            # --------------------------
            # 5️⃣  Download Button
            # --------------------------
            if st.session_state.get("fetch_excel_file") and st.session_state.fetch_excel_file.get("excel_file"):
                excel_b64 = st.session_state.fetch_excel_file["excel_file"]
                excel_bytes = base64.b64decode(excel_b64)
                saved_path = st.session_state.fetch_excel_file.get("saved_path", "resumes.xlsx")
                st.download_button(
                    label="Download Excel",
                    data=excel_bytes,
                    file_name=os.path.basename(saved_path),
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

if __name__ == "__main__":
    app()