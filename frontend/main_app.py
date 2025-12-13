import os
import base64
import requests
import streamlit as st

def safe_rerun():
                """Try to trigger a Streamlit rerun in a backwards/forwards-compatible way.

                - Prefer st.experimental_rerun() where available.
                - Otherwise change a query param (st.experimental_set_query_params) to force a rerun.
                - If neither exists, toggle a session flag as a non-crashing fallback.
                """
                try:
                    fn = getattr(st, "experimental_rerun", None)
                    if callable(fn):
                        fn()
                        return

                    # Prefer the newer query params API. Assigning to st.query_params
                    # will update the URL params and force a rerun in modern Streamlit.
                    try:
                        qp = getattr(st, "query_params", None)
                        if qp is not None:
                            import time

                            st.query_params = {"_rerun": int(time.time())}
                            return
                    except Exception:
                        # fall through to session toggle fallback
                        pass
                except Exception as e:
                    # don't raise to UI; fall back to session toggle
                    print(f"safe_rerun helper failed: {e}")

                # best-effort fallback: toggle a lightweight session-state flag
                st.session_state["_needs_rerun"] = not st.session_state.get("_needs_rerun", False)
def force_rerun():
                """More aggressive rerun: try multiple methods to force Streamlit to refresh.

                Tries, in order:
                - st.experimental_rerun()
                - st.experimental_set_query_params (if available)
                - assignment to st.query_params
                - toggling a session-state flag
                """
                try:
                    fn = getattr(st, "experimental_rerun", None)
                    if callable(fn):
                        fn()
                        return
                except Exception:
                    pass

                # try assigning st.query_params
                try:
                    import time

                    qp = getattr(st, "query_params", None)
                    if qp is not None:
                        st.query_params = {"_rerun": int(time.time())}
                        return
                except Exception:
                    pass

def app():
        # --------------------------
        # Session State Defaults
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

        # Ensure additional session keys exist to avoid Streamlit AttributeError
        if "evaluation_done" not in st.session_state:
            st.session_state.evaluation_done = False
        if "evaluation_response" not in st.session_state:
            st.session_state.evaluation_response = None
        if "results" not in st.session_state:
            st.session_state.results = None
        if "excel_file" not in st.session_state:
            st.session_state.excel_file = None
        if "jd_data" not in st.session_state:
            st.session_state.jd_data = None
        if "auth_token" not in st.session_state:
            st.session_state.auth_token = None
        if "current_user" not in st.session_state:
            st.session_state.current_user = None
        if "llm_model" not in st.session_state:
            # default model (can be overridden by sidebar)
            st.session_state.llm_model = "gemini-2.5-flash"
        if "llm_api_key" not in st.session_state:
            st.session_state.llm_api_key = None
        if "save_mode" not in st.session_state:
            st.session_state.save_mode = None
        if "show_auth" not in st.session_state:
            # When True, the sidebar shows the login/register form. Clear after login.
            st.session_state.show_auth = True
        # --------------------------
        # Session & Auth Handling
        # --------------------------
        if "auth_token" not in st.session_state:
            st.session_state.auth_token = None
        if "current_user" not in st.session_state:
            st.session_state.current_user = None

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



 
            # fallback: toggle a session flag
            st.session_state["_needs_rerun"] = not st.session_state.get("_needs_rerun", False)

        username = st.session_state.get("current_user") or "Guest"
        top_col1, top_col2 = st.columns([8, 1])
        with top_col1:
            st.subheader(f"👋 Welcome, {username}!")
        with top_col2:
            if st.button("🔄", help="Refresh app"):
                force_rerun()


        # --------------------------
        # Sidebar: Account + LLM Settings
        # --------------------------
        with st.sidebar:
            st.header("Account")
            st.markdown("---")
            st.subheader("LLM Settings (optional)")
            model_choices = {
                "Gemini 2.5 Flash (fast, recommended)": "gemini-2.5-flash",
                "Gemini 2.5 Flash Lite (higher rpd)": "gemini-2.5-flash-lite",
                "Gemini 1.5 Pro (balanced)": "gemini-1.5-pro",
                "Gemini 1.0 (smaller, cheaper)": "gemini-1.0",
                "Custom model name": "custom"
            }
            model_label = st.selectbox("Choose model", list(model_choices.keys()), index=0, key="_llm_model_select")
            selected_model_value = model_choices[model_label]
            if selected_model_value == "custom":
                custom_model = st.text_input("Custom model name", key="_llm_model_custom")
                model_value = custom_model or "gemini-2.5-flash"
            else:
                model_value = selected_model_value

            api_key_input = st.text_input("Model API Key (optional)", type="password", key="_llm_api_key")

            # persist choices in session state so other UI actions pick them up
            if model_value:
                st.session_state.llm_model = model_value
            if api_key_input:
                st.session_state.llm_api_key = api_key_input

            # Put account controls inside a sidebar container so we can explicitly clear it
            account_container = st.container()

            supports_on_submit = False
            # Callback to handle auth form submission. Using on_submit ensures
            # session_state is updated immediately and allows us to call experimental_rerun

            def _handle_auth_submit():
                auth_tab = st.session_state.get("auth_tab", "Login")
                username = st.session_state.get("_auth_username", "")
                password = st.session_state.get("_auth_password", "")
                full_name = st.session_state.get("_auth_fullname", "")

                try:
                    if auth_tab == "Register":
                        resp = requests.post(
                            "http://127.0.0.1:8000/register",
                            json={"username": username, "password": password, "full_name": full_name},
                            timeout=10,
                        )

                        if resp.status_code == 200:
                            st.success("✅ Registered! Waiting for admin approval.")
                        else:
                            st.error(resp.text)

                    else:  # LOGIN
                        resp = requests.post(
                            "http://127.0.0.1:8000/login",
                            json={"username": username, "password": password},
                            timeout=10,
                        )

                        if resp.status_code == 200:
                            token = resp.json()["access_token"]
                            st.session_state.auth_token = token
                            st.session_state.current_user = username
                            st.session_state.show_auth = False
                            force_rerun()

                        elif resp.status_code == 403:
                            st.error("⏳ Admin approval pending")

                        else:
                            st.error("❌ Invalid login")

                except Exception as e:
                    st.error(f"Auth error: {e}")



            with account_container:
                # Account controls
                if not st.session_state.get("show_auth") and st.session_state.get("current_user"):
                    # user already logged in -> show signed-in view
                    st.markdown(f"**Signed in as:** {st.session_state.current_user}")
                    if st.button("Logout", key="btn_logout"):
                        # clear session state and remove the container contents immediately
                        st.session_state.auth_token = None
                        st.session_state.current_user = None
                        st.session_state.show_auth = True
                        st.success("Logged out")
                        # best-effort immediate rerun
                        force_rerun()
                else:
                    # Use plain widgets (not st.form) to avoid Streamlit form lifecycle quirks
                    # Widgets write directly to st.session_state keys so the handler can read them.
                    st.selectbox("Action", ("Login", "Register"), key="auth_tab")
                    st.text_input("Username", key="_auth_username")
                    st.text_input("Password", type="password", key="_auth_password")
                    st.text_input("Full name (register only)", key="_auth_fullname")
                    if st.button("Submit", key="btn_auth_submit"):
                        _handle_auth_submit()
                        # Trigger a rerun so the sidebar updates immediately
                        force_rerun()
                    # LLM settings are picked from session_state keys set by the sidebar

        # --------------------------
        # Step 1: Upload Resumes
        # --------------------------
        if st.session_state.step >= 1:
            st.subheader("Upload Candidate Resumes")
            uploaded_files = st.file_uploader(
                "Upload resumes (PDF/DOCX)", type=["pdf", "docx"], accept_multiple_files=True
            )

            if uploaded_files:
                st.session_state.uploaded_files = uploaded_files
                if st.button("Upload Resume(s)", key="btn_upload_resumes"):
                    files_data = [("files", (file.name, file.getvalue())) for file in uploaded_files]
                    headers = {}
                    if st.session_state.auth_token:
                        headers["Authorization"] = f"Bearer {st.session_state.auth_token}"
                    # include llm settings if present
                    if st.session_state.get("llm_model"):
                        headers["X-Model"] = st.session_state.get("llm_model")
                    if st.session_state.get("llm_api_key"):
                        headers["X-Api-Key"] = st.session_state.get("llm_api_key")
                    response = requests.post("http://127.0.0.1:8000/upload_resumes_only", files=files_data, headers=headers)
                    if response.status_code == 200:
                        st.session_state.uploaded_paths = response.json()["uploaded_paths"]
                        st.success("✅ Resume(s) uploaded successfully!")
                        st.session_state.step = 2
                    else:
                        st.error(f"Failed to upload resumes: {response.text}")


        # --------------------------
        # Step 2: Job Description & Weights
        # --------------------------
        if st.session_state.step >= 2:
            st.subheader("Upload Job Description & Assign Weights")

            jd_file = st.file_uploader(
                "📄 Upload Job Description (PDF/DOCX)",
                type=["pdf", "docx"],
                key="jd_file"
            )

            # Upload button (only if file selected) and Skip button on one line at the top
            top_cols = st.columns([3, 1])
            upload_clicked = False
            skip_clicked = False
            with top_cols[0]:
                if jd_file:
                    upload_clicked = st.button("Upload JD")
                else:
                    st.write("")  # empty for alignment
            with top_cols[1]:
                skip_clicked = st.button("Skip JD & Proceed")

            # Handle Upload click
            if upload_clicked:
                headers = {}
                if st.session_state.auth_token:
                    headers["Authorization"] = f"Bearer {st.session_state.auth_token}"
                if st.session_state.get("llm_model"):
                    headers["X-Model"] = st.session_state.get("llm_model")
                if st.session_state.get("llm_api_key"):
                    headers["X-Api-Key"] = st.session_state.get("llm_api_key")

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
                    st.session_state.jd_fields = data.get("jd_fields", [])
                    st.session_state.jd_json = data.get("jd_json", {})
                    st.success("✅ JD processed successfully! Sliders generated.")
                else:
                    st.error(f"❌ JD upload failed: {response.text}")
                    st.stop()

            # Show sliders if available
            if "jd_fields" in st.session_state and st.session_state.jd_fields:
                st.subheader("🎚️ Assign Weights")

                weights = {}
                for field in st.session_state.jd_fields:
                    default_val = st.session_state.get("weights", {}).get(field, 0.2) * 100
                    weights[field] = st.slider(
                        f"{field.capitalize()} Weight (%)",
                        0, 100, int(default_val), 5,
                        key=f"w_{field}"
                    )

                total = sum(weights.values())
                st.markdown(f"**Total Weight Sum:** `{total}%`")

                weights = {k: round(v / 100, 2) for k, v in weights.items()}
                st.session_state.weights = weights

                # Show Proceed button next to Skip button below sliders
                bottom_cols = st.columns([2, 1])
                proceed_clicked = False
                with bottom_cols[0]:
                    proceed_clicked = st.button("Proceed to Evaluation", key="btn_proceed_jd")
                with bottom_cols[1]:
                    # Keep Skip button visible here as well, or hide to avoid duplication
                    # Optionally do nothing or show a small note
                    pass

            else:
                st.info("ℹ️ Upload a JD file to enable scoring.")
                proceed_clicked = False  # No proceed button without sliders

            # Handle Proceed button click
            if proceed_clicked:
                if not st.session_state.uploaded_paths:
                    st.warning("Please upload at least one resume before proceeding.")
                    st.stop()

                jd_data = {
                    "jd_json": st.session_state.jd_json,
                    "weights": st.session_state.weights
                }
                st.session_state.jd_data = jd_data
                st.session_state.step = 3

            # Handle Skip button click (from top)
            if skip_clicked:
                if not st.session_state.uploaded_paths:
                    st.warning("Please upload at least one resume before proceeding.")
                    st.stop()

                st.session_state.jd_data = None
                st.session_state.step = 3

        # --------------------------
        # Step 3: Evaluate Resumes
        # --------------------------
        if st.session_state.step >= 3:
            st.subheader("Evaluating Resumes...")

            if not st.session_state.evaluation_done:
                with st.spinner("⏳ Evaluating resumes... This may take a few minutes."):
                    headers = {}
                    if st.session_state.auth_token:
                        headers["Authorization"] = f"Bearer {st.session_state.auth_token}"
                    if st.session_state.get("llm_model"):
                        headers["X-Model"] = st.session_state.get("llm_model")
                    if st.session_state.get("llm_api_key"):
                        headers["X-Api-Key"] = st.session_state.get("llm_api_key")

                    payload = {
                        "uploaded_paths": st.session_state.uploaded_paths,
                        "jd_data": st.session_state.jd_data  # may be None
                    }

                    try:
                        response = requests.post(
                            "http://127.0.0.1:8000/evaluate_resumes",
                            json=payload,
                            headers=headers
                        )
                        st.session_state.evaluation_response = response
                        st.session_state.evaluation_done = True
                    except Exception as e:
                        st.error(f"⚠️ Request failed: {e}")
                        st.stop()

            # Handle backend response
            response = st.session_state.evaluation_response
            if response.status_code == 200:
                result_json = response.json()
                st.session_state.results = result_json.get("data", [])
                jd_mode = result_json.get("jd_mode", "disabled")

                if jd_mode == "enabled":
                    st.success("✅ Evaluation completed with JD scoring!")
                else:
                    st.success("✅ Resume parsing completed (no JD provided).")

                st.session_state.step = 4
            else:
                st.error(f"❌ Evaluation failed: {response.text}")

        # --------------------------
        # Step 4: Display Results
        # --------------------------
        if st.session_state.step >= 4 and st.session_state.results:
            st.subheader("Review Evaluation Results")

            for resume in st.session_state.results:
                name = resume.get("name", "Unnamed Candidate")
                with st.expander(f"▶ {name}"):
                    st.markdown(f"**Email:** {resume.get('email','')}")
                    st.markdown(f"**Phone:** {resume.get('phone','')}")
                    st.markdown(f"**Location:** {resume.get('location','')}")

                    # URLs
                    urls = resume.get("urls", [])
                    if urls:
                        st.markdown("**URLs:**")
                        for url in urls:
                            st.markdown(f"- {url}")

                    # Skills
                    skills = resume.get("skills", [])
                    if skills:
                        st.markdown("**Skills:**")
                        skill_cards = " ".join([
                            f"<span style='display:inline-block;background:#e0f7fa;color:#006064;"
                            f"padding:5px 10px;margin:3px;border-radius:8px'>{s}</span>"
                            for s in skills
                        ])
                        st.markdown(skill_cards, unsafe_allow_html=True)

                    # Education
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

                    # Experience
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

                    # Projects
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

                    # Certifications
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
                    # Summary Section
                    # --------------------------
                    st.markdown("---")
                    st.markdown("### 📊 Summary")

                    # Matched Skills
                    matched = resume.get("matched_skills", [])
                    if matched:
                        st.markdown("**✅ Matched Skills (from JD):**")
                        matched_cards = " ".join([
                            f"<span style='display:inline-block;background:#c8e6c9;color:#1b5e20;"
                            f"padding:6px 12px;margin:3px;border-radius:10px'>{s}</span>"
                            for s in matched
                        ])
                        st.markdown(matched_cards, unsafe_allow_html=True)

                    # Missing Skills
                    missing = resume.get("missing_skills", [])
                    if missing:
                        st.markdown("**⚠️ Missing Skills (from JD):**")
                        missing_cards = " ".join([
                            f"<span style='display:inline-block;background:#ffcdd2;color:#b71c1c;"
                            f"padding:6px 12px;margin:3px;border-radius:10px'>{s}</span>"
                            for s in missing
                        ])
                        st.markdown(missing_cards, unsafe_allow_html=True)

                    # Other Skills
                    other = resume.get("other_skills", [])
                    if other:
                        st.markdown("**🟡 Other Skills (not in JD):**")
                        other_cards = " ".join([
                            f"<span style='display:inline-block;background:#fff9c4;color:#f57f17;"
                            f"padding:6px 12px;margin:3px;border-radius:10px'>{s}</span>"
                            for s in other
                        ])
                        st.markdown(other_cards, unsafe_allow_html=True)

                    # Total Experience
                    exp_years = resume.get("total_experience_years", "N/A")
                    st.markdown(
                        f"<span style='display:inline-block;background:#fff8e1;color:#f57f17;"
                        f"padding:8px 14px;margin:3px;border-radius:10px;font-weight:600;'>"
                        f"🧮 Total Experience: {exp_years}</span>",
                        unsafe_allow_html=True
                    )

                    # Overall Score
                    score = resume.get("score", "N/A")
                    st.markdown(
                        f"<span style='display:inline-block;background:#e8f5e9;color:#1b5e20;"
                        f"padding:8px 14px;margin:3px;border-radius:10px;font-weight:600;'>"
                        f"🎯 Overall Score: {score}</span>",
                        unsafe_allow_html=True
                    )

                    # Remarks
                    remarks = resume.get("remarks", [])
                    if remarks:
                        st.markdown("**💬 Remarks / Feedback:**")
                        remark_cards = " ".join([
                            f"<span style='display:inline-block;background:#fce4ec;color:#880e4f;"
                            f"padding:6px 12px;margin:3px;border-radius:10px'>{r}</span>"
                            for r in remarks
                        ])
                        st.markdown(remark_cards, unsafe_allow_html=True)

                    # Scoring Breakdown
                    breakdown = resume.get("scoring_breakdown", {})
                    if breakdown:
                        st.markdown("**📈 Scoring Breakdown:**")
                        breakdown_cards = " ".join([
                            f"<span style='display:inline-block;background:#e3f2fd;color:#0d47a1;"
                            f"padding:6px 12px;margin:3px;border-radius:10px'>{k.capitalize()}: {v}</span>"
                            for k, v in breakdown.items()
                        ])
                        st.markdown(breakdown_cards, unsafe_allow_html=True)

        # --------------------------
        # Step 5: Export Options
        # --------------------------
        # if st.session_state.get("step", 0) >= 4 and st.session_state.get("results"):
        #     st.subheader("Download Evaluation Results")

        #     # --- default selection
        #     if "export_option" not in st.session_state:
        #         st.session_state.export_option = "Create New Excel File"

        #     # --- option radio
        #     st.session_state.export_option = st.radio(
        #         "Choose Export Option:",
        #         (
        #             "Create New Excel File",
        #             "Append to Existing Sheet",
        #             "Create New Sheet in Existing File",
        #             "Export to MongoDB Database",
        #         ),
        #     )

        #     # --------------------------
        #     # Utility to call backend
        #     # --------------------------
        #     def export_to_backend(params):
        #         try:
        #             headers = {}
        #             if st.session_state.get("auth_token"):
        #                 headers["Authorization"] = f"Bearer {st.session_state.auth_token}"
        #             if st.session_state.get("llm_model"):
        #                 headers["X-Model"] = st.session_state.llm_model
        #             if st.session_state.get("llm_api_key"):
        #                 headers["X-Api-Key"] = st.session_state.llm_api_key

        #             response = requests.post(
        #                 "http://127.0.0.1:8000/export_resumes_excel",
        #                 json=params,
        #                 headers=headers,
        #                 timeout=120
        #             )

        #             if response.status_code == 200:
        #                 resp_json = response.json()
        #                 if resp_json.get("status") == "success" and resp_json.get("excel_file"):
        #                     st.session_state.excel_file = resp_json
        #                     st.success("✅ Export successful!")
        #                 else:
        #                     st.warning(f"❌ Export failed: {resp_json.get('message', 'Unknown error')}")
        #             else:
        #                 st.warning(f"❌ Backend returned status {response.status_code}")

        #         except Exception as e:
        #             st.error(f"❌ Exception during export: {e}")

        #     # --------------------------
        #     # 1️⃣  Create New Excel File
        #     # --------------------------
        #     if st.session_state.export_option == "Create New Excel File":
        #         st.session_state.save_mode = "new_file"
        #         file_name = st.text_input("Enter Excel File Name", "resumes.xlsx")
        #         sheet_name = st.text_input("Enter Sheet Name", "Sheet1")

        #         if st.button("Export New Excel", key="btn_export_new"):
        #           #  file_path = os.path.join(EXPORTS_DIR, file_name)
        #             params = {
        #                 "processed_resumes": st.session_state.results,
        #                 "mode": "new_file",
        #                 "file_path": file_name,
        #                 "sheet_name": sheet_name,
        #             }
        #             export_to_backend(params)
        #     # # --------------------------
        #     # # 2️⃣  Append to Existing Sheet
        #     # # --------------------------
        #     # elif st.session_state.export_option == "Append to Existing Sheet":
        #     #     st.session_state.save_mode = "append_sheet"
        #     #     excel_files = [f for f in os.listdir(EXPORTS_DIR) if f.endswith(".xlsx")]

        #     #     if excel_files:
        #     #         selected_file = st.selectbox("Select Existing Excel File", excel_files)
        #     #         if selected_file:
        #     #             file_path = os.path.join(EXPORTS_DIR, selected_file)
        #     #             wb = load_workbook(file_path)
        #     #             selected_sheet = st.selectbox("Select Existing Sheet", wb.sheetnames)

        #     #             if st.button("Append to Sheet", key="btn_append_sheet"):
        #     #                 params = {
        #     #                     "processed_resumes": st.session_state.results,
        #     #                     "mode": "append_sheet",
        #     #                     "file_path": file_path,
        #     #                     "sheet_name": selected_sheet,
        #     #                 }
        #     #                 export_to_backend(params)
        #     #     else:
        #     #         st.warning("No existing Excel files found in your exports folder.")

        #     # # --------------------------
        #     # # 3️⃣  Create New Sheet in Existing File
        #     # # --------------------------
        #     # elif st.session_state.export_option == "Create New Sheet in Existing File":
        #     #     st.session_state.save_mode = "new_sheet"
        #     #     excel_files = [f for f in os.listdir(EXPORTS_DIR) if f.endswith(".xlsx")]

        #     #     if excel_files:
        #     #         selected_file = st.selectbox("Select Existing Excel File", excel_files)
        #     #         if selected_file:
        #     #             file_path = os.path.join(EXPORTS_DIR, selected_file)
        #     #             new_sheet = st.text_input("Enter New Sheet Name", "Sheet1")

        #     #             if st.button("Create New Sheet", key="btn_create_sheet"):
        #     #                 params = {
        #     #                     "processed_resumes": st.session_state.results,
        #     #                     "mode": "new_sheet",
        #     #                     "file_path": file_path,
        #     #                     "sheet_name": new_sheet,
        #     #                 }
        #     #                 export_to_backend(params)
        #     #     else:
        #     #         st.warning("No existing Excel files found in your exports folder.")

        #     # # # --------------------------
        #     # 4️⃣  Export to MongoDB
        #     # --------------------------
        #     elif st.session_state.export_option == "Export to MongoDB Database":
        #         st.session_state.save_mode = "mongo"
        #         mongo_url = st.text_input("MongoDB Connection URL", "")
        #         db_name = st.text_input("Database Name", "resume_db")
        #         collection_name = st.text_input("Collection Name", "resumes")

        #         if st.button("Export to MongoDB", key="btn_export_mongo"):
        #             if not mongo_url:
        #                 st.error("Please enter a valid MongoDB URL.")
        #             else:
        #                 params = {
        #                     "processed_resumes": st.session_state.results,
        #                     "mongo_url": mongo_url,
        #                     "db_name": db_name,
        #                     "collection_name": collection_name,
        #                 }

        #                 headers = {}
        #                 if st.session_state.get("auth_token"):
        #                     headers["Authorization"] = f"Bearer {st.session_state.auth_token}"

        #                 with st.spinner("⏳ Uploading resumes to MongoDB..."):
        #                     try:
        #                         response = requests.post(
        #                             "http://127.0.0.1:8000/export_resumes_mongo",
        #                             json=params,
        #                             headers=headers,
        #                             timeout=120,
        #                         )
        #                         resp_json = response.json()
        #                         if resp_json.get("status") == "success":
        #                             st.success(f"✅ Exported {resp_json.get('inserted_count')} resumes to MongoDB.")
        #                         else:
        #                             st.warning(f"❌ Export failed: {resp_json.get('message', 'Unknown error')}")
        #                     except Exception as e:
        #                         st.error(f"❌ Exception during export: {e}")

        #     # --------------------------
        #     # 5️⃣  Download Button
        #     # --------------------------
        #     if st.session_state.get("excel_file") and st.session_state.excel_file.get("excel_file"):
        #         excel_b64 = st.session_state.excel_file["excel_file"]
        #         excel_bytes = base64.b64decode(excel_b64)
        #         saved_path = st.session_state.excel_file.get("saved_path", "resumes.xlsx")
        #         st.download_button(
        #             label="Download Excel",
        #             data=excel_bytes,
        #             file_name=os.path.basename(saved_path),
        #             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        #         )

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

        if st.session_state.get("step", 0) >= 4 and st.session_state.get("results"):
            st.subheader("Download Evaluation Results")

            # --- default selection
            if "export_option" not in st.session_state:
                st.session_state.export_option = "Create New Excel File"

            # --- option radio
            st.session_state.export_option = st.radio(
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
                            st.session_state.excel_file = resp_json
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
            if st.session_state.export_option == "Create New Excel File":
                st.session_state.save_mode = "new_file"
                file_name = st.text_input("Enter Excel File Name", "resumes.xlsx")
                sheet_name = st.text_input("Enter Sheet Name", "Sheet1")

                if st.button("Export New Excel", key="btn_export_new"):
                    params = {
                        "processed_resumes": st.session_state.results,
                        "mode": "new_file",
                        "file_path": file_name,
                        "sheet_name": sheet_name,
                    }
                    export_to_backend(params)

            # --------------------------
            # 2️⃣  Append to Existing Sheet
            # --------------------------
            elif st.session_state.export_option == "Append to Existing Sheet":
                st.session_state.save_mode = "append_sheet"

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
                                "processed_resumes": st.session_state.results,
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
            elif st.session_state.export_option == "Create New Sheet in Existing File":
                st.session_state.save_mode = "new_sheet"

                excel_files = fetch_user_export_files()

                if excel_files:
                    selected_file = st.selectbox("Select Existing Excel File", excel_files)
                    if selected_file:
                        new_sheet = st.text_input("Enter New Sheet Name", "Sheet1")

                        if new_sheet and st.button("Create New Sheet", key="btn_create_sheet"):
                            params = {
                                "processed_resumes": st.session_state.results,
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
            elif st.session_state.export_option == "Export to MongoDB Database":
                st.session_state.save_mode = "mongo"
                mongo_url = st.text_input("MongoDB Connection URL", "")
                db_name = st.text_input("Database Name", "resume_db")
                collection_name = st.text_input("Collection Name", "resumes")

                if st.button("Export to MongoDB", key="btn_export_mongo"):
                    if not mongo_url:
                        st.error("Please enter a valid MongoDB URL.")
                    else:
                        params = {
                            "processed_resumes": st.session_state.results,
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
            if st.session_state.get("excel_file") and st.session_state.excel_file.get("excel_file"):
                excel_b64 = st.session_state.excel_file["excel_file"]
                excel_bytes = base64.b64decode(excel_b64)
                saved_path = st.session_state.excel_file.get("saved_path", "resumes.xlsx")
                st.download_button(
                    label="Download Excel",
                    data=excel_bytes,
                    file_name=os.path.basename(saved_path),
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )


if __name__ == "__main__":
    app()


