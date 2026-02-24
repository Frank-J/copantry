import streamlit as st


def apply_sidebar_style():
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            min-width: 210px !important;
            max-width: 210px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
