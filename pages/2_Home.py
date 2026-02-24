import streamlit as st
from utils import apply_sidebar_style
from database import (
    get_ingredients,
    get_recipes,
    get_cookable_recipes,
    get_forgotten_ingredients,
    get_most_cooked_recipes,
    get_most_used_ingredients,
)
from gemini_client import generate_home_insight

st.set_page_config(page_title="Home", page_icon="🏠", layout="wide")
apply_sidebar_style()

st.title("🏠 Home")
st.markdown("Your fridge and recipe overview at a glance.")

st.divider()

# Load data
ingredients = get_ingredients()
recipes = get_recipes()
cookable = get_cookable_recipes()
forgotten = get_forgotten_ingredients()

# KPI Cards
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Ingredients in Pantry", len(ingredients))
with col2:
    st.metric("Saved Recipes", len(recipes))
with col3:
    st.metric("Recipes You Can Make Now", len(cookable))
with col4:
    st.metric("Ingredients Not in Any Recipe", len(forgotten))

st.divider()

# AI Insights — auto-generate on first load, cached for the session
st.subheader("💡 Today's Insights")

if "home_insight" not in st.session_state:
    if not ingredients:
        st.session_state["home_insight"] = "Add some ingredients to your fridge to get personalised insights."
    elif not recipes:
        st.session_state["home_insight"] = "Add some recipes to get personalised insights based on your fridge."
    else:
        with st.spinner("Generating insights based on your fridge..."):
            try:
                st.session_state["home_insight"] = generate_home_insight(
                    ingredients, recipes, cookable, forgotten
                )
            except Exception as e:
                st.session_state["home_insight"] = f"Could not generate insights: {e}"

st.markdown(st.session_state["home_insight"])

if st.button("Refresh Insights"):
    del st.session_state["home_insight"]
    st.rerun()

st.divider()

# Usage stats + forgotten ingredients
col1, col2 = st.columns(2)

with col1:
    st.subheader("🍳 Most Cooked Recipes")
    most_cooked = get_most_cooked_recipes()
    if not most_cooked:
        st.info("No cooking history yet.")
        st.page_link("pages/4_Recipes.py", label="Mark a recipe as cooked →")
    else:
        for item in most_cooked:
            st.write(f"**{item['name']}** — cooked {item['count']} time(s)")

with col2:
    st.subheader("🥕 Most Used Ingredients")
    most_used = get_most_used_ingredients()
    if not most_used:
        st.info("No cooking history yet.")
    else:
        for item in most_used:
            st.write(f"**{item['name']}** — used {item['count']} time(s)")

st.divider()

# Recipes cookable now
st.subheader("✅ Recipes You Can Make Right Now")
if not cookable:
    if not ingredients:
        st.info("Add ingredients to your fridge to see what you can cook.")
        st.page_link("pages/3_Pantry.py", label="Go to Pantry →")
    elif not recipes:
        st.info("Add some recipes to see which ones you can make with your current ingredients.")
        st.page_link("pages/4_Recipes.py", label="Add a Recipe →")
    else:
        st.info("None of your saved recipes are fully covered by your current pantry ingredients.")
else:
    for recipe in cookable:
        st.write(f"- **{recipe['name']}** ({recipe['cooking_time']})")

st.divider()

# Forgotten ingredients
st.subheader("⚠️ Ingredients Not in Any Recipe")
if not forgotten:
    if not ingredients:
        st.info("No ingredients in your pantry yet.")
        st.page_link("pages/3_Pantry.py", label="Go to Pantry →")
    else:
        st.success("All your fridge ingredients are used in at least one saved recipe.")
else:
    st.warning(
        f"{len(forgotten)} ingredient(s) in your fridge aren't part of any saved recipe — "
        "consider adding recipes that use them or removing them from your fridge."
    )
    for ing in forgotten:
        st.write(f"- **{ing['name']}** ({ing['amount']} {ing['unit']})")
