# import requests
# import streamlit as st
# from utils import force_rerun

# def auth_page():
#     # ---------- Center layout ----------
#     left, center, right = st.columns([1, 2, 1])

#     with center:
#         # Title - bigger and centered, no card around it
#         st.markdown(
#             """
#             <style>
#             .auth-title {
#                 text-align: center;
#                 font-size: 36px;
#                 font-weight: 700;
#                 margin-bottom: 10px;
#             }
#             .auth-subtitle {
#                 text-align: center;
#                 color: #9aa0a6;
#                 margin-bottom: 25px;
#                 font-size: 16px;
#             }
#             </style>
#             """,
#             unsafe_allow_html=True,
#         )
#         st.markdown('<div class="auth-title">Resume Screening System</div>', unsafe_allow_html=True)
#         st.markdown('<div class="auth-subtitle">Login or create an account</div>', unsafe_allow_html=True)

#         tabs = st.tabs(["Login", "Register"])

#         # ---------------- LOGIN ----------------
#         with tabs[0]:
#             username = st.text_input("Username", key="login_user")
#             password = st.text_input("Password", type="password", key="login_pass")

#             if st.button("Login", use_container_width=True):
#                 resp = requests.post(
#                     "http://127.0.0.1:8000/auth/login",
#                     json={"username": username, "password": password},
#                     timeout=10,
#                 )

#                 if resp.status_code == 200:
#                     st.session_state.auth_token = resp.json()["access_token"]
#                     st.session_state.current_user = username
#                     st.session_state.user_role = resp.json().get("role", "user")
#                     force_rerun()
#                 elif resp.status_code == 403:
#                     st.error("⏳ Admin approval pending")
#                 else:
#                     st.error("❌ Invalid credentials")

#         # ---------------- REGISTER ----------------
#         with tabs[1]:
#             username = st.text_input("Username", key="reg_user")
#             password = st.text_input("Password", type="password", key="reg_pass")
#             full_name = st.text_input("Full name", key="reg_name")

#             if st.button("Register", use_container_width=True):
#                 resp = requests.post(
#                     "http://127.0.0.1:8000/auth/register",
#                     json={
#                         "username": username,
#                         "password": password,
#                         "full_name": full_name,
#                     },
#                     timeout=10,
#                 )

#                 if resp.status_code == 200:
#                     st.success("✅ Registered. Wait for admin approval.")
#                 else:
#                     st.error(resp.text)
# import requests
# import streamlit as st
# from utils import force_rerun

# def auth_page():
#     # ---------- Center layout ----------
#     left, center, right = st.columns([1, 2, 1])

#     with center:
#         # Title - bigger and centered, no card around it
#         st.markdown(
#             """
#             <style>
#             .auth-title {
#                 text-align: center;
#                 font-size: 36px;
#                 font-weight: 700;
#                 margin-bottom: 10px;
#             }
#             .auth-subtitle {
#                 text-align: center;
#                 color: #9aa0a6;
#                 margin-bottom: 25px;
#                 font-size: 16px;
#             }
#             </style>
#             """,
#             unsafe_allow_html=True,
#         )
#         st.markdown('<div class="auth-title">Resume Screening System</div>', unsafe_allow_html=True)
#         st.markdown('<div class="auth-subtitle">Login or create an account</div>', unsafe_allow_html=True)

#         tabs = st.tabs(["Login", "Register"])

#         # ---------------- LOGIN ----------------
#         with tabs[0]:
#             username = st.text_input("Username", key="login_user")
#             password = st.text_input("Password", type="password", key="login_pass")

#             st.button(
#                 "Login",
#                 use_container_width=True,
#                 on_click=login,
#                 args=(username, password),
#             )

#         # ---------------- REGISTER ----------------
#         with tabs[1]:
#             reg_username = st.text_input("Username", key="reg_user")
#             reg_password = st.text_input("Password", type="password", key="reg_pass")
#             full_name = st.text_input("Full name", key="reg_name")

#             st.button(
#                 "Register",
#                 use_container_width=True,
#                 on_click=register,
#                 args=(reg_username, reg_password, full_name),
#             )


# def login(username, password):
#     resp = requests.post(
#         "http://127.0.0.1:8000/auth/login",
#         json={"username": username, "password": password},
#         timeout=10,
#     )
#     if resp.status_code == 200:
#         st.session_state.auth_token = resp.json()["access_token"]
#         st.session_state.current_user = username
#         st.session_state.user_role = resp.json().get("role", "user")
#         force_rerun()
#     elif resp.status_code == 403:
#         st.error("⏳ Admin approval pending")
#     else:
#         st.error("❌ Invalid credentials")

# def register(username, password, full_name):
#     resp = requests.post(
#         "http://127.0.0.1:8000/auth/register",
#         json={
#             "username": username,
#             "password": password,
#             "full_name": full_name,
#         },
#         timeout=10,
#     )
#     if resp.status_code == 200:
#         st.success("✅ Registered. Wait for admin approval.")
#     else:
#         st.error(resp.text)
import requests
import streamlit as st
from utils import force_rerun

def auth_app():
    # ---------- Center layout ----------
    left, center, right = st.columns([1, 2, 1])

    with center:
        # Title - bigger and centered, no card around it
        st.markdown(
            """
            <style>
            .auth-title {
                text-align: center;
                font-size: 36px;
                font-weight: 700;
                margin-bottom: 10px;
            }
            .auth-subtitle {
                text-align: center;
                color: #9aa0a6;
                margin-bottom: 25px;
                font-size: 16px;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="auth-title">Resume Screening System</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-subtitle">Login or create an account</div>', unsafe_allow_html=True)

        tabs = st.tabs(["Login", "Register"])

        # ---------------- LOGIN ----------------
        with tabs[0]:
            with st.form("login_form", clear_on_submit=False):
                username = st.text_input("Username", key="login_user")
                password = st.text_input("Password", type="password", key="login_pass")
                submitted = st.form_submit_button("Login", use_container_width=True)
                if submitted:
                    login(username, password)

        # ---------------- REGISTER ----------------
        with tabs[1]:
            with st.form("register_form", clear_on_submit=False):
                reg_username = st.text_input("Username", key="reg_user")
                reg_password = st.text_input("Password", type="password", key="reg_pass")
                full_name = st.text_input("Full name", key="reg_name")
                submitted = st.form_submit_button("Register", use_container_width=True)
                if submitted:
                    register(reg_username, reg_password, full_name)


def login(username, password):
    resp = requests.post(
        "http://127.0.0.1:8000/auth/login",
        json={"username": username, "password": password},
        timeout=20,
    )
    if resp.status_code == 200:
        st.session_state.auth_token = resp.json()["access_token"]
        st.session_state.current_user = username
        st.session_state.user_role = resp.json().get("role", "user")
        force_rerun()
    elif resp.status_code == 403:
        st.error("⏳ Admin approval pending")
    else:
        st.error("❌ Invalid credentials")

def register(username, password, full_name):
    resp = requests.post(
        "http://127.0.0.1:8000/auth/register",
        json={
            "username": username,
            "password": password,
            "full_name": full_name,
        },
        timeout=20,
    )
    if resp.status_code == 200:
        st.success("✅ Registered. Wait for admin approval.")
    else:
        st.error(resp.text)
