import streamlit as st


def apply_sidebar_style():
    st.markdown(
        """
        <style>
        a {
            text-decoration: underline !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
