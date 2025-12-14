# import streamlit as st
# import main_app
# import fetch_from_db_app
# import admin_app
# from main_app import force_rerun
# st.set_page_config(layout="wide")

# CARD_STYLE = """
#     <style>
#     .card {
#         background-color: #f9f9f9;
#         color: #222222;
#         border-radius: 10px;
#         padding: 20px;
#         margin: 10px 10px 30px 10px;
#         box-shadow: 0 4px 8px 0 rgba(0,0,0,0.1);
#         transition: 0.3s;
#         height: 200px;  /* fixed height for equal size */
#         display: flex;
#         flex-direction: column;
#         justify-content: space-between;
#     }
#     .card:hover {
   
#         box-shadow:
#             0 8px 16px rgba(0, 0, 0, 0.6),      /* black shadow */
#             0 0 25px rgba(0, 102, 255, 0.6); 
#     }
#     .card-title {
#         font-size: 26px;
#         font-weight: 700;
#         margin-bottom: 15px;
#         color: #111111;
#         flex-shrink: 0; /* prevent shrinking */
#     }
#     .card-content {
#         font-size: 16px;
#         line-height: 1.5;
#         margin-bottom: 20px;
#         color: #222222;
#         flex-grow: 1; /* take remaining space */
#         overflow-y: auto; /* scroll if overflow */
#     }
#     .full-width-title {
#         font-size: 48px;
#         font-weight: 800;
#         text-align: center;
#         margin-bottom: 40px;
#         color: #FFFFFF;
#         width: 100%;
#         user-select: none;
#     }
#     </style>
# """

# def show_homepage():
#     st.markdown(CARD_STYLE, unsafe_allow_html=True)
#     st.markdown('<div class="full-width-title">Resume Screening System - Home Page</div>', unsafe_allow_html=True)

#     col1, col2, col3 = st.columns(3, gap="large")

#     with col1:
#         st.markdown("""
#             <div class="card">
#                 <div class="card-title">📤 Upload & Approve Resume</div>
#                 <div class="card-content">
#                     <ul>
#                         <li>Upload resumes in bulk</li>
#                         <li>Automatic parsing & screening</li>
#                         <li>Admin approval workflow</li>
#                     </ul>
#                 </div>
#             </div>
#         """, unsafe_allow_html=True)
#         if st.button("Go to Upload & Approve", key="upload_btn"):
#             st.session_state['selected_app'] = "upload"

#     with col2:
#         st.markdown("""
#             <div class="card">
#                 <div class="card-title">📂 Fetch Resumes from DB</div>
#                 <div class="card-content">
#                     <ul>
#                         <li>Search and filter resumes</li>
#                         <li>View candidate details</li>
#                         <li>Export data easily</li>
#                     </ul>
#                 </div>
#             </div>
#         """, unsafe_allow_html=True)
#         if st.button("Go to Fetch from DB", key="fetch_btn"):
#             st.session_state['selected_app'] = "fetch"

#     with col3:
#         st.markdown("""
#             <div class="card">
#                 <div class="card-title">🛠 Admin Panel</div>
#                 <div class="card-content">
#                     <ul>
#                         <li>Manage user roles</li>
#                         <li>Approve or deny registrations</li>
#                         <li>Monitor system activity</li>
#                     </ul>
#                 </div>
#             </div>
#         """, unsafe_allow_html=True)
#         if st.button("Go to Admin Panel", key="admin_btn"):
#             st.session_state['selected_app'] = "admin"


# def main():
#     # Initialize the key with None if missing
#     if 'selected_app' not in st.session_state:
#         st.session_state.selected_app = None

#     if not st.session_state.selected_app:
#         # If no app selected, show homepage
#         show_homepage()
#     else:
#         # Show Back button on top for navigation
#         if st.button("⬅️ Back to Home"):
#             st.session_state.selected_app = None
#             force_rerun()

#         # Show the selected app UI only
#         if st.session_state.selected_app == "upload":
#             main_app.app()
#         elif st.session_state.selected_app == "fetch":
#             fetch_from_db_app.app()
#         elif st.session_state.selected_app == "admin":
#             admin_app.app()


# if __name__ == "__main__":
#     main()
# import streamlit as st
# import main_app
# import fetch_from_db_app
# import admin_app
# from main_app import force_rerun

# st.set_page_config(layout="wide")

# # --------------------------
# # Card Styles
# # --------------------------
# CARD_STYLE = """
# <style>
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
#     height: 220px;
#     display: flex;
#     flex-direction: column;
#     justify-content: space-between;
#     cursor: pointer;
# }

# .card:hover {
#     box-shadow:
#         0 8px 16px rgba(0, 0, 0, 0.6),
#         0 0 25px rgba(0, 102, 255, 0.6);
# }

# .card-title {
#     font-size: 26px;
#     font-weight: 700;
#     margin-bottom: 15px;
# }

# .card-content {
#     font-size: 16px;
#     line-height: 1.5;
#     flex-grow: 1;
# }

# .full-width-title {
#     font-size: 48px;
#     font-weight: 800;
#     text-align: center;
#     margin-bottom: 40px;
#     color: #FFFFFF;
#     user-select: none;
# }

# .invisible-btn {
#     position: absolute;
#     top: 0;
#     left: 0;
#     width: 100%;
#     height: 100%;
#     opacity: 0;
# }
# </style>
# """


# # --------------------------
# # Homepage
# # --------------------------
# def show_homepage():
#     st.markdown(CARD_STYLE, unsafe_allow_html=True)
#     st.markdown(
#         '<div class="full-width-title">Resume Screening System</div>',
#         unsafe_allow_html=True
#     )

#     col1, col2, col3 = st.columns(3, gap="large")

#     with col1:
#         st.markdown("""
#         <div class="card-wrapper">
#             <div class="card">
#                 <div class="card-title">📤 Upload & Approve Resumes</div>
#                 <div class="card-content">
#                     <ul>
#                         <li>Upload resumes in bulk</li>
#                         <li>Automatic screening</li>
#                         <li>Approval workflow</li>
#                     </ul>
#                 </div>
#             </div>
#         </div>
#         """, unsafe_allow_html=True)

#         if st.button("", key="upload_card"):
#             reset_service_state("upload")
#             st.session_state.selected_app = "upload"
#             force_rerun()

#     with col2:
#         st.markdown("""
#         <div class="card-wrapper">
#             <div class="card">
#                 <div class="card-title">📂 Fetch Resumes from DB</div>
#                 <div class="card-content">
#                     <ul>
#                         <li>Search resumes</li>
#                         <li>Filter candidates</li>
#                         <li>Export results</li>
#                     </ul>
#                 </div>
#             </div>
#         </div>
#         """, unsafe_allow_html=True)

#         if st.button("", key="fetch_card"):
#             reset_service_state("fetch")
#             st.session_state.selected_app = "fetch"
#             force_rerun()

#     with col3:
#         st.markdown("""
#         <div class="card-wrapper">
#             <div class="card">
#                 <div class="card-title">🛠 Admin Panel</div>
#                 <div class="card-content">
#                     <ul>
#                         <li>User management</li>
#                         <li>Approvals</li>
#                         <li>System monitoring</li>
#                     </ul>
#                 </div>
#             </div>
#         </div>
#         """, unsafe_allow_html=True)

#         if st.button("", key="admin_card"):
#             reset_service_state("admin")
#             st.session_state.selected_app = "admin"
#             force_rerun()

# # --------------------------
# # Main Router
# # --------------------------
# def main():
#     if "selected_app" not in st.session_state:
#         st.session_state.selected_app = None

#     if not st.session_state.selected_app:
#         show_homepage()
#     else:
#         if st.button("⬅️ Back to Home"):
#             reset_service_state(st.session_state.selected_app)
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

import streamlit as st
import main_app
import fetch_from_db_app
import admin_app
from main_app import force_rerun

st.set_page_config(layout="wide")

# --------------------------
# Card Styles
# --------------------------
CARD_STYLE = """
<style>
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
    height: 220px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    cursor: pointer;
}

.card:hover {
    box-shadow:
        0 8px 16px rgba(0, 0, 0, 0.6),
        0 0 25px rgba(0, 102, 255, 0.6);
}

.card-title {
    font-size: 26px;
    font-weight: 700;
    margin-bottom: 15px;
}

.card-content {
    font-size: 16px;
    line-height: 1.5;
    flex-grow: 1;
}

.full-width-title {
    font-size: 48px;
    font-weight: 800;
    text-align: center;
    margin-bottom: 40px;
    color: #FFFFFF;
    user-select: none;
}
</style>
"""

# --------------------------
# Homepage
# --------------------------
def show_homepage():
    st.markdown(CARD_STYLE, unsafe_allow_html=True)
    st.markdown(
        '<div class="full-width-title">Resume Screening System</div>',
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3, gap="large")

    with col1:
        st.markdown("""
        <div class="card-wrapper">
            <div class="card">
                <div class="card-title">📤 Upload & Approve Resumes</div>
                <div class="card-content">
                    <ul>
                        <li>Upload resumes in bulk</li>
                        <li>Automatic screening</li>
                        <li>Approval workflow</li>
                    </ul>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("", key="upload_card"):
            st.session_state.selected_app = "upload"
            force_rerun()

    with col2:
        st.markdown("""
        <div class="card-wrapper">
            <div class="card">
                <div class="card-title">📂 Fetch Resumes from DB</div>
                <div class="card-content">
                    <ul>
                        <li>Search resumes</li>
                        <li>Filter candidates</li>
                        <li>Export results</li>
                    </ul>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("", key="fetch_card"):
            st.session_state.selected_app = "fetch"
            force_rerun()

    with col3:
        st.markdown("""
        <div class="card-wrapper">
            <div class="card">
                <div class="card-title">🛠 Admin Panel</div>
                <div class="card-content">
                    <ul>
                        <li>User management</li>
                        <li>Approvals</li>
                        <li>System monitoring</li>
                    </ul>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("", key="admin_card"):
            st.session_state.selected_app = "admin"
            force_rerun()

# --------------------------
# Main Router
# --------------------------
def main():
    if "selected_app" not in st.session_state:
        st.session_state.selected_app = None

    if not st.session_state.selected_app:
        show_homepage()

    else:
        # ⬅️ Back Navigation + Explicit Reset
        if st.button("⬅️ Back to Home"):
            if st.session_state.selected_app == "fetch":
                fetch_from_db_app.reset_fetch_state()
            elif st.session_state.selected_app == "upload":
                main_app.reset_upload_state()
            elif st.session_state.selected_app == "admin":
                admin_app.reset_admin_state()

            st.session_state.selected_app = None
            force_rerun()

        # Route to service
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
