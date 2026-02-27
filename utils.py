import streamlit as st
from datetime import date


def get_local_date():
    """Return today's date in the user's browser timezone.
    Falls back to server date if JS hasn't resolved yet."""
    try:
        from streamlit_js_eval import streamlit_js_eval
        from zoneinfo import ZoneInfo
        from datetime import datetime
        tz_name = streamlit_js_eval(
            js_expressions="Intl.DateTimeFormat().resolvedOptions().timeZone",
            key="browser_tz",
        )
        if tz_name:
            return datetime.now(ZoneInfo(tz_name)).date()
    except Exception:
        pass
    return date.today()


def apply_sidebar_style():
    st.markdown(
        """
        <style>
        /* Underline links in main content */
        [data-testid="stMain"] a {
            text-decoration: underline !important;
        }
        /* But not sidebar navigation links */
        [data-testid="stSidebar"] a {
            text-decoration: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
