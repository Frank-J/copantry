import streamlit as st
from datetime import datetime
from database import get_ingredients, add_ingredient, delete_ingredient, update_ingredient_amount
from constants import UNITS
from utils import apply_sidebar_style
from gemini_client import get_storage_tips

st.set_page_config(page_title="Pantry", page_icon="🥫", layout="wide")
apply_sidebar_style()

st.title("🥫 My Pantry")
st.markdown("Track all the ingredients you have at home — fridge, freezer, and pantry.")

st.divider()

# Add ingredient form
st.subheader("Add Ingredient")
with st.form("add_ingredient_form", clear_on_submit=True):
    col1, col2, col3 = st.columns([3, 2, 2])
    with col1:
        name = st.text_input("Ingredient Name", placeholder="e.g. Eggs")
    with col2:
        amount = st.number_input("Amount", min_value=0.1, value=1.0, step=0.5)
    with col3:
        unit = st.selectbox("Unit", UNITS)

    submitted = st.form_submit_button("Add to Pantry", use_container_width=True)
    if submitted:
        if name.strip():
            add_ingredient(name.strip(), amount, unit)
            st.success(f"Added {amount} {unit} of {name}!")
            if "storage_tips_key" in st.session_state:
                del st.session_state["storage_tips_key"]  # invalidate cache
            st.rerun()
        else:
            st.error("Please enter an ingredient name.")

st.divider()

# Current ingredients list
st.subheader("Current Ingredients")
ingredients = get_ingredients()


def format_dates(added_str, updated_str):
    def rel(dt):
        delta = datetime.now() - dt
        if delta.days == 0:
            return "today"
        elif delta.days == 1:
            return "yesterday"
        elif delta.days < 7:
            return f"{delta.days}d ago"
        else:
            return dt.strftime("%b %d")
    try:
        added = datetime.fromisoformat(added_str)
        label = f"Added {rel(added)}"
        if updated_str and updated_str != added_str:
            updated = datetime.fromisoformat(updated_str)
            label += f" · Updated {rel(updated)}"
        return label
    except Exception:
        return ""


if not ingredients:
    st.info("Your pantry is empty. Add some ingredients above.")
else:
    # Load storage tips (cached by ingredient name set)
    ingredient_names = [i["name"] for i in ingredients]
    cache_key = tuple(sorted(ingredient_names))
    if st.session_state.get("storage_tips_key") != cache_key:
        with st.spinner("Loading storage tips..."):
            try:
                tips = get_storage_tips(ingredient_names)
                st.session_state["storage_tips"] = tips
            except Exception:
                st.session_state["storage_tips"] = {}
            st.session_state["storage_tips_key"] = cache_key
    tips = st.session_state.get("storage_tips", {})

    # Column headers
    hcol1, hcol2, hcol3, hcol4, hcol5 = st.columns([3, 2, 3, 1, 1])
    with hcol1:
        st.markdown("**Ingredient**")
    with hcol2:
        st.markdown("**Amount**")
    with hcol3:
        st.markdown("**Date**")
    st.divider()

    for ingredient in ingredients:
        col1, col2, col3, col4, col5 = st.columns([3, 2, 3, 1, 1])
        with col1:
            st.write(f"**{ingredient['name']}**")
        with col2:
            st.write(f"{ingredient['amount']} {ingredient['unit']}")
        with col3:
            st.caption(format_dates(ingredient["added_date"], ingredient.get("updated_date")))
        with col4:
            if st.button("Edit", key=f"edit_btn_{ingredient['id']}"):
                st.session_state["editing_id"] = ingredient["id"]
        with col5:
            if st.button("Remove", key=f"del_{ingredient['id']}"):
                delete_ingredient(ingredient["id"])
                if st.session_state.get("editing_id") == ingredient["id"]:
                    del st.session_state["editing_id"]
                if "storage_tips_key" in st.session_state:
                    del st.session_state["storage_tips_key"]
                st.rerun()

        # Storage tip
        tip = tips.get(ingredient["name"])
        if tip:
            st.caption(f"ℹ️ {tip}")

        # Inline edit form
        if st.session_state.get("editing_id") == ingredient["id"]:
            with st.form(f"edit_form_{ingredient['id']}"):
                new_amount = st.number_input(
                    f"New amount for {ingredient['name']}",
                    min_value=0.1,
                    value=float(ingredient["amount"]),
                    step=0.5,
                )
                col_save, col_cancel = st.columns(2)
                with col_save:
                    if st.form_submit_button("Save", use_container_width=True):
                        update_ingredient_amount(ingredient["id"], new_amount)
                        del st.session_state["editing_id"]
                        st.rerun()
                with col_cancel:
                    if st.form_submit_button("Cancel", use_container_width=True):
                        del st.session_state["editing_id"]
                        st.rerun()
