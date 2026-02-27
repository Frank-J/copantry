import streamlit as st
from datetime import date


def get_local_date(tz_offset=None):
    """Return today's date in the user's timezone.
    tz_offset: minutes returned by JS getTimezoneOffset() (e.g. 480 for PST).
    Falls back to server date if not provided."""
    if tz_offset is not None:
        from datetime import datetime, timezone, timedelta
        tz = timezone(timedelta(minutes=-int(tz_offset)))
        return datetime.now(tz).date()
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
