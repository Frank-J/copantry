import streamlit as st
from datetime import date


def get_local_date():
    """Return today's date in the user's browser timezone.
    Falls back to server date if JS hasn't resolved yet."""
    try:
        from streamlit_js_eval import streamlit_js_eval
        from datetime import datetime, timezone, timedelta
        # getTimezoneOffset() returns minutes behind UTC (e.g. PST = +480)
        offset = streamlit_js_eval(
            js_expressions="new Date().getTimezoneOffset()",
            key="tz_offset",
        )
        if offset is not None:
            tz = timezone(timedelta(minutes=-int(offset)))
            return datetime.now(tz).date()
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
