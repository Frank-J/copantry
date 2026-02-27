import streamlit as st
from datetime import date, timedelta
from utils import apply_sidebar_style, get_local_date
from database import (
    initialize_db,
    get_recipes,
    get_shopping_plan,
    get_meal_entries,
    get_shopping_list_items,
    add_shopping_list_item,
    toggle_shopping_list_item,
    delete_shopping_list_item,
    clear_checked_shopping_items,
)

initialize_db()

st.set_page_config(page_title="CoPantry · Shopping List", page_icon="🛒", layout="wide")
apply_sidebar_style()

st.title("🛒 Shopping List")
st.markdown("What you need to buy — derived from your meal plan, plus anything you add manually.")

st.divider()

recipes = get_recipes()
today = get_local_date()

# ---------------------------------------------------------------------------
# Section 1: Meal plan-driven items
# ---------------------------------------------------------------------------
st.subheader("📅 From Your Meal Plan")

UNPLANNED = "— Unplanned —"
SPECIAL = [UNPLANNED, "🍽️ Eating Out", "🏖️ Vacation / Skip"]

next7_entries = get_meal_entries(today.isoformat(), (today + timedelta(days=6)).isoformat())
home_meals_flat = {}
for day_str, day_meals in next7_entries.items():
    for mt, val in day_meals.items():
        if val not in SPECIAL:
            home_meals_flat[f"{day_str}_{mt}"] = val

if not home_meals_flat:
    st.info("No home meals planned for the next 7 days.")
    st.page_link("pages/4_Meal_Planner.py", label="Go to Meal Planner →")
elif not recipes:
    st.info("No recipes saved yet.")
    st.page_link("pages/2_Recipes.py", label="Add a Recipe →")
else:
    plan = get_shopping_plan(home_meals_flat, recipes)

    if plan["fully_covered"]:
        st.success("✅ Your pantry covers all planned meals this week — nothing to buy.")
    else:
        shop_by = date.fromisoformat(plan["shop_by"])
        days_until = (shop_by - today).days
        if days_until <= 0:
            st.error(f"⚠️ Shop today — you're already running short on some items.")
        elif days_until == 1:
            st.warning(f"🛒 Shop tomorrow — running short soon.")
        else:
            st.info(f"🗓️ Shop by **{shop_by.strftime('%A, %b %-d')}**")

        # Display as a table
        rows = []
        for item in plan["items"]:
            rows.append({
                "Ingredient": item["name"],
                "Need": f"{item['need_amount']} {item['need_unit']}",
                "Have": f"{item['have_amount']} {item['have_unit']}",
                "Runs out": date.fromisoformat(item["runs_out_on"]).strftime("%a %b %-d"),
                "For": item["recipe"],
            })
        st.table(rows)

        # Download
        lines = [f"Shopping List — shop by {shop_by.strftime('%A, %b %-d')}", ""]
        for item in plan["items"]:
            lines.append(
                f"- {item['name']}: need {item['need_amount']} {item['need_unit']} "
                f"(have {item['have_amount']} {item['have_unit']}) "
                f"for {item['recipe']}"
            )
        st.download_button(
            label="Download Shopping List",
            data="\n".join(lines),
            file_name="shopping_list.txt",
            mime="text/plain",
        )

st.divider()

# ---------------------------------------------------------------------------
# Section 2: Manual items checklist
# ---------------------------------------------------------------------------
st.subheader("📝 My List")
st.caption("Add anything else you need — household items, extras, or ingredients not in your meal plan.")

# Add item form
with st.form("add_item_form", clear_on_submit=True):
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        new_item = st.text_input("Item", placeholder="e.g. Paper towels", label_visibility="collapsed")
    with col_btn:
        add_submitted = st.form_submit_button("Add", use_container_width=True)
    if add_submitted and new_item.strip():
        add_shopping_list_item(new_item.strip())
        st.rerun()

# Display checklist
items = get_shopping_list_items()

if not items:
    st.caption("No items yet — add something above.")
else:
    checked_count = sum(1 for i in items if i["checked"])

    for item in items:
        col_check, col_name, col_del = st.columns([0.5, 5, 0.5])
        with col_check:
            new_state = st.checkbox(
                "",
                value=item["checked"],
                key=f"check_{item['id']}",
                label_visibility="collapsed",
            )
            if new_state != item["checked"]:
                toggle_shopping_list_item(item["id"], new_state)
                st.rerun()
        with col_name:
            if item["checked"]:
                st.markdown(f"~~{item['name']}~~")
            else:
                st.write(item["name"])
        with col_del:
            if st.button("✕", key=f"del_{item['id']}", help="Remove"):
                delete_shopping_list_item(item["id"])
                st.rerun()

    if checked_count > 0:
        st.write("")
        if st.button(f"Clear {checked_count} checked item{'s' if checked_count > 1 else ''}", type="secondary"):
            clear_checked_shopping_items()
            st.rerun()
