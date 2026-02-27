import streamlit as st
from database import get_ingredients, get_recipes, get_cookable_recipes
from gemini_client import suggest_recipes
from utils import apply_sidebar_style

st.set_page_config(page_title="CoPantry · Suggestions", page_icon="💡", layout="wide")
apply_sidebar_style()

st.title("💡 Suggestions")
st.markdown("See what you can cook right now, or get AI ideas based on what's in your pantry.")

st.divider()

ingredients = get_ingredients()
recipes = get_recipes()

if not ingredients:
    st.warning("Your pantry is empty — add some ingredients to get suggestions.")
    st.page_link("pages/1_Pantry.py", label="Go to Pantry →")
else:
    # Section 1: Can cook right now
    st.subheader("✅ Recipes You Can Make Right Now")
    cookable = get_cookable_recipes()
    if not cookable:
        st.info("None of your saved recipes are fully covered by your current pantry.")
    else:
        for recipe in cookable:
            st.write(f"- **{recipe['name']}** ({recipe['cooking_time']})")

    st.divider()

    # Section 2: AI suggestions
    st.subheader("✨ AI Recipe Ideas")
    st.markdown("**Currently in your pantry:**")
    pantry_summary = ", ".join([f"{i['name']} ({i['amount']} {i['unit']})" for i in ingredients])
    st.write(pantry_summary)

    if not recipes:
        st.info("You have no saved recipes yet. Suggestions will still work, but adding recipes gives better results.")
        st.page_link("pages/2_Recipes.py", label="Add a Recipe →")

    st.write("")
    if st.button("Get AI Recipe Suggestions", use_container_width=True, type="primary"):
        with st.spinner("Thinking about what you can cook..."):
            suggestions = suggest_recipes(ingredients, recipes)
            st.session_state["suggestions"] = suggestions

    if "suggestions" in st.session_state:
        st.markdown(st.session_state["suggestions"])
