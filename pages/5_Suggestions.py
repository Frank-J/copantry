import streamlit as st
from database import get_ingredients, get_recipes
from gemini_client import suggest_recipes
from utils import apply_sidebar_style

st.set_page_config(page_title="Suggestions", page_icon="💡", layout="wide")
apply_sidebar_style()

st.title("💡 Recipe Suggestions")
st.markdown("Get AI-powered recipe ideas based on what's in your fridge.")

st.divider()

ingredients = get_ingredients()
recipes = get_recipes()

if not ingredients:
    st.warning("Your pantry is empty — add some ingredients to get suggestions.")
    st.page_link("pages/3_Pantry.py", label="Go to Pantry →")
else:
    st.markdown("**Currently in your fridge:**")
    fridge_summary = ", ".join([f"{i['name']} ({i['amount']} {i['unit']})" for i in ingredients])
    st.write(fridge_summary)

    if not recipes:
        st.info("You have no saved recipes yet. Suggestions will still work, but adding recipes gives better results.")
        st.page_link("pages/4_Recipes.py", label="Add a Recipe →")

    st.divider()

    if st.button("Get Recipe Suggestions", use_container_width=True, type="primary"):
        with st.spinner("Thinking about what you can cook..."):
            suggestions = suggest_recipes(ingredients, recipes)
            st.session_state["suggestions"] = suggestions

    if "suggestions" in st.session_state:
        st.markdown(st.session_state["suggestions"])
