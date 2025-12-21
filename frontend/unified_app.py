import streamlit as st
from auth_app import auth_page
import main_app
import fetch_from_db_app
import admin_app
from main_app import force_rerun

st.set_page_config(layout="wide")

# --------------------------
# Styles
# --------------------------
CARD_STYLE = """
<style>

/* ---------- Navbar ---------- */
.navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 24px;
    background-color: #0E1117;
    border-bottom: 1px solid #2A2A2A;
    margin-bottom: 25px;
}

.nav-left {
    font-size: 20px;
    font-weight: 700;
    color: #FFFFFF;
}

.nav-right {
    font-size: 14px;
    color: #CCCCCC;
}

/* ---------- Cards ---------- */
.card-wrapper {
    position: relative;
}

.card {
    background-color: #f9f9f9;
    color: #222222;
    border-radius: 12px;
    padding: 20px;
    margin: 10px 10px 30px 10px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    transition: 0.3s;
    height: 240px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.card:hover {
    box-shadow:
        0 12px 24px rgba(0, 0, 0, 0.85),
        0 0 35px rgba(0, 102, 255, 0.75);
    transform: translateY(-3px);
}

.card-title {
    font-size: 24px;
    font-weight: 700;
    margin-bottom: 12px;
}

.card-content {
    font-size: 15px;
    line-height: 1.5;
    flex-grow: 1;
}

/* ---------- Title ---------- */
.full-width-title {
    font-size: 44px;
    font-weight: 800;
    text-align: center;
    margin-bottom: 10px;
    color: #FFFFFF;
}

.subtitle {
    text-align: center;
    font-size: 18px;
    color: #D0D0D0;
    margin-bottom: 30px;
}
</style>
"""

# --------------------------
# Navbar (HOME ONLY)
# --------------------------
def render_navbar():
    st.markdown(
        f"""
        <div class="navbar">
            <div class="nav-left">Resume Screening System</div>
            <div class="nav-right">
                {st.session_state.get("current_user")} ({st.session_state.get("user_role")})
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    def logout():
        for key in ["auth_token", "current_user", "selected_app", "show_auth"]:
            if key in st.session_state:
                del st.session_state[key]
        force_rerun()

    col_spacer, col_logout = st.columns([6, 0.5])
    with col_logout:
        st.button("Logout", on_click=logout)

# --------------------------
# Homepage
# --------------------------
def show_homepage():
    # 🔒 Safety gate (same logic as old code)
    if not st.session_state.get("auth_token"):
        return

    render_navbar()
    st.markdown(CARD_STYLE, unsafe_allow_html=True)

    # st.markdown(
    #     '<div class="full-width-title">Resume Screening System</div>',
    #     unsafe_allow_html=True
    # )
    st.markdown(
        '<div class="subtitle">AI-driven resume parsing, evaluation, and candidate management</div>',
        unsafe_allow_html=True
    )

    user_role = st.session_state.get("user_role", "user")
    is_admin = user_role == "admin"

    upload_card_html = """
    <div class="card-wrapper">
        <div class="card">
            <div class="card-title">📤 Upload & Evaluate Resume Files</div>
            <div class="card-content">
                <ul>
                    <li>Upload PDF or DOCX resumes</li>
                    <li>Evaluate resumes using a Job Description</li>
                    <li>Generate structured resume JSON</li>
                    <li>Export to Excel or store in MongoDB</li>
                </ul>
            </div>
        </div>
    </div>
    """

    fetch_card_html = """
    <div class="card-wrapper">
        <div class="card">
            <div class="card-title">📂 Fetch & Evaluate Resumes from Database</div>
            <div class="card-content">
                <ul>
                    <li>Fetch parsed resume JSONs</li>
                    <li>Evaluate candidates using Job Description</li>
                    <li>Export to excel or store in MongoDB</li>
                </ul>
            </div>
        </div>
    </div>
    """

    admin_card_html = """
    <div class="card-wrapper">
        <div class="card">
            <div class="card-title">🛠 User & Access Management</div>
            <div class="card-content">
                <ul>
                    <li>Manage system users</li>
                    <li>Approve or revoke access</li>
                    <li>Assign roles and permissions</li>
                </ul>
            </div>
        </div>
    </div>
    """

    if is_admin:
        col1, col2, col3 = st.columns(3, gap="large")

        with col1:
            st.markdown(upload_card_html, unsafe_allow_html=True)
            btn_spacer_l, btn_col, btn_spacer_r = st.columns([1, 2, 1])
            with btn_col:
                def on_upload_click():
                    st.session_state.selected_app= "upload"
                    force_rerun()
                st.button("Upload & Evaluate", on_click=on_upload_click, key="upload_btn")


        with col2:
            st.markdown(fetch_card_html, unsafe_allow_html=True)
            btn_spacer_l, btn_col, btn_spacer_r = st.columns([1, 2, 1])
            with btn_col:
                def on_fetch_click():
                    st.session_state.selected_app= "fetch"
                    force_rerun()
                st.button("Fetch & Evaluate", on_click=on_fetch_click, key="fetch_btn")

        with col3:
            st.markdown(admin_card_html, unsafe_allow_html=True)
            btn_spacer_l, btn_col, btn_spacer_r = st.columns([1, 2, 1])
            with btn_col:
                def on_admin_click():
                    st.session_state.selected_app= "admin"
                    force_rerun()
                st.button("Open Admin Panel", on_click=on_admin_click, key="admin_btn")

    else:
        spacer_l, col1, col2, spacer_r = st.columns([1, 2, 2, 1])

        with col1:
            st.markdown(upload_card_html, unsafe_allow_html=True)
            btn_spacer_l, btn_col, btn_spacer_r = st.columns([1, 2, 1])
            with btn_col:
                def on_upload_click():
                    st.session_state.selected_app= "upload"
                    force_rerun()
                st.button("Upload & Evaluate", on_click=on_upload_click, key="upload_btn")


        with col2:
            st.markdown(fetch_card_html, unsafe_allow_html=True)
            btn_spacer_l, btn_col, btn_spacer_r = st.columns([1, 2, 1])
            with btn_col:
                def on_fetch_click():
                    st.session_state.selected_app= "fetch"
                    force_rerun()
                st.button("Fetch & Evaluate", on_click=on_fetch_click, key="fetch_btn")


# --------------------------
# Main
# --------------------------
def main():
    # 🔒 AUTH GATE — FIRST
    if not st.session_state.get("auth_token"):
        auth_page()
        return

    if "selected_app" not in st.session_state:
        st.session_state.selected_app = None

    if not st.session_state.selected_app:
        show_homepage()
    else:
        def back_to_home():
            if st.session_state.selected_app == "fetch":
                fetch_from_db_app.reset_fetch_state()
            elif st.session_state.selected_app == "upload":
                main_app.reset_upload_state()
            elif st.session_state.selected_app == "admin":
                admin_app.reset_admin_state()
            st.session_state.selected_app = None
            force_rerun()

        st.button("⬅️ Back to Home", on_click=back_to_home)

        if st.session_state.selected_app == "upload":
            main_app.app()
        elif st.session_state.selected_app == "fetch":
            fetch_from_db_app.app()
        elif st.session_state.selected_app == "admin":
            admin_app.app()

# --------------------------
# Entry
# --------------------------
if __name__ == "__main__":
    main()
# import streamlit as st
# from auth_app import auth_page
# import main_app
# import fetch_from_db_app
# import admin_app
# from main_app import force_rerun

# st.set_page_config(layout="wide")

# # --------------------------
# # Styles
# # --------------------------
# CARD_STYLE = """
# <style>
# /* ---------- Cards ---------- */
# .card-wrapper {
#     position: relative;
# }

# .card {
#     background-color: #f9f9f9;
#     color: #222222;
#     border-radius: 12px;
#     padding: 20px;
#     margin: 10px 10px 30px 10px;
#     box-shadow: 0 4px 8px rgba(0,0,0,0.1);
#     transition: 0.3s;
#     height: 240px;
#     display: flex;
#     flex-direction: column;
#     justify-content: space-between;
# }

# .card:hover {
#     box-shadow:
#         0 12px 24px rgba(0, 0, 0, 0.85),
#         0 0 35px rgba(0, 102, 255, 0.75);
#     transform: translateY(-3px);
# }

# .card-title {
#     font-size: 24px;
#     font-weight: 700;
#     margin-bottom: 12px;
# }

# .card-content {
#     font-size: 15px;
#     line-height: 1.5;
#     flex-grow: 1;
# }

# /* ---------- Title ---------- */
# .full-width-title {
#     font-size: 44px;
#     font-weight: 800;
#     text-align: center;
#     margin-bottom: 10px;
#     color: #FFFFFF;
# }

# .subtitle {
#     text-align: center;
#     font-size: 18px;
#     color: #D0D0D0;
#     margin-bottom: 30px;
# }

# /* ---------- User info & logout ---------- */
# .user-logout-row {
#     display: flex;
#     justify-content: flex-end;
#     align-items: center;
#     margin-bottom: 20px;
#     color: #CCCCCC;
#     font-size: 14px;
# }

# .user-info {
#     margin-right: 15px;
#     user-select: none;
# }

# .logout-button button {
#     padding: 6px 12px;
#     font-size: 14px;
#     border-radius: 6px;
#     cursor: pointer;
#     background-color: #f63366;
#     color: white;
#     border: none;
# }
# </style>
# """

# # --------------------------
# # Homepage
# # --------------------------
# def show_homepage():
#     # 🔒 Safety gate
#     if not st.session_state.get("auth_token"):
#         return

#     st.markdown(CARD_STYLE, unsafe_allow_html=True)

#     # User info + Logout button at top right
#     col1, col2, col3 = st.columns([6, 1, 0.7])
#     with col2:
#         st.markdown(f'<div class="user-info">{st.session_state.get("current_user", "")} ({st.session_state.get("user_role", "")})</div>', unsafe_allow_html=True)
#     with col3:
#         if st.button("Logout"):
#             for key in ["auth_token", "current_user", "selected_app", "show_auth", "user_role"]:
#                 if key in st.session_state:
#                     del st.session_state[key]
#             force_rerun()

#     st.markdown(
#         '<div class="full-width-title">Resume Screening System</div>',
#         unsafe_allow_html=True
#     )
#     st.markdown(
#         '<div class="subtitle">AI-driven resume parsing, evaluation, and candidate management</div>',
#         unsafe_allow_html=True
#     )

#     user_role = st.session_state.get("user_role", "user")
#     is_admin = user_role == "admin"

#     upload_card_html = """
#     <div class="card-wrapper">
#         <div class="card">
#             <div class="card-title">📤 Upload & Evaluate Resume Files</div>
#             <div class="card-content">
#                 <ul>
#                     <li>Upload PDF or DOCX resumes</li>
#                     <li>Evaluate resumes using a Job Description</li>
#                     <li>Generate structured resume JSON</li>
#                     <li>Export to Excel or store in MongoDB</li>
#                 </ul>
#             </div>
#         </div>
#     </div>
#     """

#     fetch_card_html = """
#     <div class="card-wrapper">
#         <div class="card">
#             <div class="card-title">📂 Fetch & Evaluate Resumes from Database</div>
#             <div class="card-content">
#                 <ul>
#                     <li>Fetch parsed resume JSONs</li>
#                     <li>Evaluate candidates using Job Description</li>
#                     <li>Export to Excel or store in MongoDB</li>
#                 </ul>
#             </div>
#         </div>
#     </div>
#     """

#     admin_card_html = """
#     <div class="card-wrapper">
#         <div class="card">
#             <div class="card-title">🛠 User & Access Management</div>
#             <div class="card-content">
#                 <ul>
#                     <li>Manage system users</li>
#                     <li>Approve or revoke access</li>
#                     <li>Assign roles and permissions</li>
#                 </ul>
#             </div>
#         </div>
#     </div>
#     """

#     # Button callbacks for single click navigation
#     def on_upload_click():
#         st.session_state.selected_app = "upload"
#         force_rerun()

#     def on_fetch_click():
#         st.session_state.selected_app = "fetch"
#         force_rerun()

#     def on_admin_click():
#         st.session_state.selected_app = "admin"
#         force_rerun()

#     if is_admin:
#         col1, col2, col3 = st.columns(3, gap="large")

#         with col1:
#             st.markdown(upload_card_html, unsafe_allow_html=True)
#             st.button("Upload & Evaluate", on_click=on_upload_click, key="upload_btn")

#         with col2:
#             st.markdown(fetch_card_html, unsafe_allow_html=True)
#             st.button("Fetch & Evaluate", on_click=on_fetch_click, key="fetch_btn")

#         with col3:
#             st.markdown(admin_card_html, unsafe_allow_html=True)
#             st.button("Open Admin Panel", on_click=on_admin_click, key="admin_btn")

#     else:
#         spacer_l, col1, col2, spacer_r = st.columns([1, 2, 2, 1])

#         with col1:
#             st.markdown(upload_card_html, unsafe_allow_html=True)
#             st.button("Upload & Evaluate", on_click=on_upload_click, key="upload_btn_user")

#         with col2:
#             st.markdown(fetch_card_html, unsafe_allow_html=True)
#             st.button("Fetch & Evaluate", on_click=on_fetch_click, key="fetch_btn_user")

# # --------------------------
# # Main
# # --------------------------
# def main():
#     # 🔒 AUTH GATE — FIRST
#     if not st.session_state.get("auth_token"):
#         auth_page()
#         return

#     if "selected_app" not in st.session_state:
#         st.session_state.selected_app = None

#     if not st.session_state.selected_app:
#         show_homepage()
#     else:
#         if st.button("⬅️ Back to Home"):
#             if st.session_state.selected_app == "fetch":
#                 fetch_from_db_app.reset_fetch_state()
#             elif st.session_state.selected_app == "upload":
#                 main_app.reset_upload_state()
#             elif st.session_state.selected_app == "admin":
#                 admin_app.reset_admin_state()

#             st.session_state.selected_app = None
#             force_rerun()

#         if st.session_state.selected_app == "upload":
#             main_app.app()
#         elif st.session_state.selected_app == "fetch":
#             fetch_from_db_app.app()
#         elif st.session_state.selected_app == "admin":
#             admin_app.app()

# # --------------------------
# # Entry
# # --------------------------
# if __name__ == "__main__":
#     main()
