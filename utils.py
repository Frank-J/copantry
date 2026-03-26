import streamlit as st
from datetime import date
from constants import AI_DAILY_LIMIT
from database import get_ai_usage_today


def get_local_date():
    return date.today()


def show_ai_limit_message():
    """Show a toast + inline warning when the daily AI quota is exhausted."""
    st.toast("Daily AI limit reached. Check back tomorrow.", icon="⚠️")
    st.warning(
        "**Daily AI limit reached.** "
        "CoPantry uses Google Gemini AI to power features like recipe extraction, meal planning suggestions, and pantry insights. "
        "To manage API costs, there is a shared daily limit of 50 AI calls across all visitors. "
        "Today's limit has been reached. All AI features will be available again tomorrow. "
        "If you are evaluating this app and would like a live demo, feel free to reach out directly."
    )


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

    usage = get_ai_usage_today()
    remaining = AI_DAILY_LIMIT - usage
    if usage >= AI_DAILY_LIMIT:
        indicator = "🔴"
        label = "limit reached"
    elif usage >= int(AI_DAILY_LIMIT * 0.8):
        indicator = "🟡"
        label = f"{remaining} remaining"
    else:
        indicator = "🟢"
        label = f"{remaining} remaining"

    st.sidebar.markdown("---")
    st.sidebar.caption(f"{indicator} AI usage: {usage}/{AI_DAILY_LIMIT} today · {label}")
