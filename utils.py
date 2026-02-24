import streamlit as st


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
