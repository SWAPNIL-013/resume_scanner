import os
import requests
import streamlit as st

def app():
    # --------------------------
    # Session & Auth Handling
    # --------------------------
    if "auth_token" not in st.session_state:
        st.session_state.auth_token = None
    if "current_user" not in st.session_state:
        st.session_state.current_user = None
    if "show_auth" not in st.session_state:
        st.session_state.show_auth = True
    if "page" not in st.session_state:
        st.session_state.page = 1
    if "last_search_query" not in st.session_state:
        st.session_state.last_search_query = ""

    def force_rerun():
        try:
            st.experimental_rerun()
        except Exception:
            st.session_state["_needs_rerun"] = not st.session_state.get("_needs_rerun", False)

    # Sidebar: Login/Register and LLM Settings (optional)
    with st.sidebar:
        st.header("Account")
        if not st.session_state.show_auth and st.session_state.current_user:
            st.markdown(f"**Signed in as:** {st.session_state.current_user}")
            if st.button("Logout"):
                st.session_state.auth_token = None
                st.session_state.current_user = None
                st.session_state.show_auth = True
                force_rerun()
        else:
            auth_tab = st.selectbox("Action", ("Login", "Register"), key="auth_tab")
            username = st.text_input("Username", key="_auth_username")
            password = st.text_input("Password", type="password", key="_auth_password")
            full_name = ""
            if auth_tab == "Register":
                full_name = st.text_input("Full name", key="_auth_fullname")
            if st.button("Submit"):
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
                    else:  # Login
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

    # Fetch current username or Guest
    username = st.session_state.get("current_user") or "Guest"
    st.subheader(f"👋 Welcome, {username}!")

    # Admin Panel - only show if logged in
    if st.session_state.get("current_user") and st.session_state.get("auth_token"):
        headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}

        try:
            resp = requests.get("http://127.0.0.1:8000/admin/users", headers=headers)
            if resp.status_code == 200:
                users = resp.json()

                total_users = sum(u["role"] == "user" for u in users)
                total_admins = sum(u["role"] == "admin" for u in users)

                st.markdown("## 🛡 Admin User Management Panel")
                st.caption("Approve, decline, and manage user roles")

                count_cols = st.columns(2)
                count_cols[0].markdown(f"**Total Users:** {total_users}")
                count_cols[1].markdown(f"**Total Admins:** {total_admins}")

                st.markdown("---")

                # Search box
                search_query = st.text_input("🔍 Search username or role", "")
                if search_query != st.session_state.last_search_query:
                    st.session_state.page = 1
                    st.session_state.last_search_query = search_query

                filtered_users = [
                    u for u in users
                    if search_query.lower() in u["username"].lower() or search_query.lower() in u["role"].lower()
                ] if search_query else users

                PAGE_SIZE = 10
                total_pages = max(1, (len(filtered_users) + PAGE_SIZE - 1) // PAGE_SIZE)
                start_idx = (st.session_state.page - 1) * PAGE_SIZE
                page_users = filtered_users[start_idx:start_idx + PAGE_SIZE]

                # Table header
                cols = st.columns([2, 1.5, 2, 1.5, 3])
                cols[0].markdown("**Username**")
                cols[1].markdown("**Role**")
                cols[2].markdown("**Status**")
                cols[3].markdown("**Actions**")
                cols[4].markdown("**Change Role**")
                st.markdown("---")

                status_color = {True: "green", False: "red", None: "orange"}

                for user in page_users:
                    cols = st.columns([2, 1.5, 2, 1.5, 3])
                    cols[0].markdown(f"👤 **{user['username']}**")
                    cols[1].markdown(f"`{user['role']}`")

                    approved = user.get("is_approved")
                    status_text = (
                        "✅ Approved" if approved else
                        ("❌ Declined" if approved is False else "⏳ Pending")
                    )
                    cols[2].markdown(
                        f"<span style='color:{status_color[approved]}'>{status_text}</span>",
                        unsafe_allow_html=True
                    )

                    if approved is not True:
                        if cols[3].button("✅", key=f"approve_{user['username']}", help="Approve user"):
                            requests.post(f"http://127.0.0.1:8000/admin/approve/{user['username']}", headers=headers)
                            force_rerun()
                    if approved is not False:
                        if cols[3].button("❌", key=f"decline_{user['username']}", help="Decline user"):
                            requests.post(f"http://127.0.0.1:8000/admin/deny/{user['username']}", headers=headers)
                            force_rerun()

                    role_col1, role_col2 = cols[4].columns([2, 1])
                    new_role = role_col1.selectbox(
                        "role",
                        ["user", "admin"],
                        index=0 if user["role"] == "user" else 1,
                        key=f"role_{user['username']}",
                        label_visibility="collapsed"
                    )
                    if role_col2.button("🔁", key=f"change_role_{user['username']}", help="Update Role"):
                        requests.post(
                            f"http://127.0.0.1:8000/admin/change-role/{user['username']}?role={new_role}",
                            headers=headers
                        )
                        force_rerun()

                    st.markdown("---")

                # Pagination controls
                pag_cols = st.columns([1, 2, 1])
                if pag_cols[0].button("⬅ Previous") and st.session_state.page > 1:
                    st.session_state.page -= 1
                    force_rerun()
                pag_cols[1].markdown(f"Page {st.session_state.page} of {total_pages}")
                if pag_cols[2].button("Next ➡") and st.session_state.page < total_pages:
                    st.session_state.page += 1
                    force_rerun()
            else:
                st.error(f"Failed to fetch users: {resp.status_code}")
        except Exception as e:
            st.error(f"Admin panel error: {e}")
    else:
        st.warning("Please log in to access the admin panel.")
if __name__ == "__main__":
    app()


