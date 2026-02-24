import streamlit as st
from database import get_recipes, get_ingredients
from gemini_client import generate_shopping_list

st.set_page_config(page_title="Shopping List", page_icon="🛒", layout="wide")

st.title("🛒 Shopping List")
st.markdown("Find out what you need to buy to make a specific recipe.")

st.divider()

recipes = get_recipes()
fridge = get_ingredients()

if not recipes:
    st.warning("No saved recipes yet — add some recipes to generate a shopping list.")
    st.page_link("pages/4_Recipes.py", label="Add a Recipe →")
else:
    recipe_names = [r["name"] for r in recipes]
    selected_name = st.selectbox("Choose a recipe to shop for:", recipe_names)

    # Clear shopping list when selected recipe changes
    if st.session_state.get("shopping_list_recipe") != selected_name:
        st.session_state["shopping_list_recipe"] = selected_name
        if "shopping_list" in st.session_state:
            del st.session_state["shopping_list"]

    selected_recipe = next(r for r in recipes if r["name"] == selected_name)

    with st.expander("Recipe Ingredients"):
        for ing in selected_recipe["ingredients"]:
            st.write(f"- {ing['name']}: {ing['amount']} {ing['unit']}")

    if not fridge:
        st.info("Your fridge is empty — the shopping list will include all recipe ingredients.")
        st.page_link("pages/3_Fridge.py", label="Add Fridge Ingredients →")

    if st.button("Generate Shopping List", use_container_width=True, type="primary"):
        with st.spinner("Checking your fridge..."):
            result = generate_shopping_list(selected_recipe, fridge)
            st.session_state["shopping_list"] = result

    if "shopping_list" in st.session_state:
        st.divider()
        st.markdown(st.session_state["shopping_list"])
        st.download_button(
            label="Download Shopping List",
            data=st.session_state["shopping_list"],
            file_name="shopping_list.txt",
            mime="text/plain",
            use_container_width=True,
        )
