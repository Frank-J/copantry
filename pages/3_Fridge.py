import streamlit as st
from datetime import datetime
from database import get_ingredients, add_ingredient, delete_ingredient, update_ingredient_amount
from constants import UNITS

st.set_page_config(page_title="Fridge", page_icon="🧊", layout="wide")

st.title("🧊 My Fridge")
st.markdown("Track the ingredients you currently have available.")

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

    submitted = st.form_submit_button("Add to Fridge", use_container_width=True)
    if submitted:
        if name.strip():
            add_ingredient(name.strip(), amount, unit)
            st.success(f"Added {amount} {unit} of {name}!")
            st.rerun()
        else:
            st.error("Please enter an ingredient name.")

st.divider()

# Current ingredients list
st.subheader("Current Ingredients")
ingredients = get_ingredients()


def format_date(date_str):
    try:
        date = datetime.fromisoformat(date_str)
        delta = datetime.now() - date
        if delta.days == 0:
            return "Added today"
        elif delta.days == 1:
            return "Added yesterday"
        elif delta.days < 7:
            return f"Added {delta.days} days ago"
        else:
            return f"Added {date.strftime('%b %d')}"
    except Exception:
        return ""


if not ingredients:
    st.info("Your fridge is empty. Add some ingredients above.")
else:
    for ingredient in ingredients:
        col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 1, 1])
        with col1:
            st.write(f"**{ingredient['name']}**")
        with col2:
            st.write(f"{ingredient['amount']} {ingredient['unit']}")
        with col3:
            st.caption(format_date(ingredient["added_date"]))
        with col4:
            if st.button("Edit", key=f"edit_btn_{ingredient['id']}"):
                st.session_state["editing_id"] = ingredient["id"]
        with col5:
            if st.button("Remove", key=f"del_{ingredient['id']}"):
                delete_ingredient(ingredient["id"])
                if st.session_state.get("editing_id") == ingredient["id"]:
                    del st.session_state["editing_id"]
                st.rerun()

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
