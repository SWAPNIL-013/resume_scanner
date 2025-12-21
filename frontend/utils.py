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
