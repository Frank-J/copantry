import streamlit as st
from utils import apply_sidebar_style

st.set_page_config(page_title="CoPantry · Feedback", page_icon="💬", layout="wide")
apply_sidebar_style()

st.title("💬 Feedback")
st.markdown("Your feedback helps improve this app. It takes about 2 minutes.")

st.divider()

st.markdown("""
Whether you found something confusing, something you loved, or something you'd change —
I'd genuinely like to hear it. This app was built to solve a real problem, and real feedback
is the best way to make it better.
""")

st.link_button(
    "Open Feedback Form →",
    url="https://forms.gle/wK3Yfhkee9kcvmjf7",
    use_container_width=True,
    type="primary",
)

st.divider()

st.markdown("""
**What the form covers:**
- Overall rating
- What you found most useful
- What you'd improve
- Any other comments

All fields except the rating are optional.
""")
