import streamlit as st
from datetime import date, timedelta
from utils import apply_sidebar_style
from database import (
    initialize_db,
    get_ingredients,
    get_recipes,
    get_cookable_recipes,
    get_forgotten_ingredients,
    get_most_cooked_recipes,
    get_most_used_ingredients,
    get_meals_for_date,
    get_meal_entries,
    get_shopping_plan,
)

initialize_db()
from gemini_client import generate_home_insight

st.set_page_config(page_title="CoPantry · Home", page_icon="🏠", layout="wide")
apply_sidebar_style()

st.title("🏠 Home")

# ---------------------------------------------------------------------------
# Load shared data
# ---------------------------------------------------------------------------
today = date.today()
ingredients = get_ingredients()
recipes = get_recipes()
recipe_map = {r["name"]: r for r in recipes}

# ---------------------------------------------------------------------------
# Section 1: Today
# ---------------------------------------------------------------------------
day_name = today.strftime("%A")
date_label = today.strftime("%B %-d")
st.markdown(f"## Today — {day_name}, {date_label}")

today_meals = get_meals_for_date(today.isoformat())

UNPLANNED = "— Unplanned —"
MEAL_ICONS = {"Breakfast": "🌅", "Lunch": "☀️", "Dinner": "🌙"}

col_b, col_l, col_d = st.columns(3)
for col, meal_type in zip([col_b, col_l, col_d], ["Breakfast", "Lunch", "Dinner"]):
    icon = MEAL_ICONS[meal_type]
    meal = today_meals.get(meal_type, UNPLANNED)
    with col:
        st.markdown(f"**{icon} {meal_type}**")
        if meal == UNPLANNED:
            st.caption("— Unplanned —")
        else:
            st.write(meal)

all_unplanned_today = all(v == UNPLANNED for v in today_meals.values())
if all_unplanned_today:
    st.caption("Nothing planned yet. [Go to Meal Planner →](pages/4_Meal_Planner)")

# ---------------------------------------------------------------------------
# Section 2: Ahead of Time (prep reminders)
# ---------------------------------------------------------------------------
thaw_reminders = []

# Build freezer ingredient map from pantry
freezer_items = {i["name"].lower(): i["name"] for i in ingredients if (i.get("location") or "Fridge") == "Freezer"}

if freezer_items and recipes:
    # Check tomorrow and day after for planned meals needing frozen ingredients
    for days_ahead in [1, 2]:
        check_date = today + timedelta(days=days_ahead)
        check_meals = get_meals_for_date(check_date.isoformat())
        check_day_label = check_date.strftime("%A")

        for meal_type, meal_name in check_meals.items():
            if meal_name == UNPLANNED or meal_name.startswith("🍽️") or meal_name.startswith("🏖️"):
                continue
            recipe = recipe_map.get(meal_name)
            if not recipe:
                continue
            for ing in recipe["ingredients"]:
                ing_key = ing["name"].lower()
                if ing_key in freezer_items:
                    display_name = freezer_items[ing_key]
                    if days_ahead == 1:
                        thaw_reminders.append(
                            f"❄️ Take **{display_name}** out of the freezer today — needed for **{meal_name}** tomorrow ({check_day_label})"
                        )
                    else:
                        thaw_reminders.append(
                            f"❄️ Take **{display_name}** out tomorrow — needed for **{meal_name}** on {check_day_label}"
                        )

# Shopping reminder — use next 7 days of planned meals
next7_entries = get_meal_entries(today.isoformat(), (today + timedelta(days=6)).isoformat())
home_meals_flat = {}
for day_str, day_meals in next7_entries.items():
    for mt, val in day_meals.items():
        if val != UNPLANNED and not val.startswith("🍽️") and not val.startswith("🏖️"):
            home_meals_flat[f"{day_str}_{mt}"] = val

shop_plan = None
if home_meals_flat:
    shop_plan = get_shopping_plan(home_meals_flat, recipes)

shopping_reminder = None
if shop_plan and not shop_plan["fully_covered"]:
    shop_by = date.fromisoformat(shop_plan["shop_by"])
    days_until = (shop_by - today).days
    top_items = [item["name"] for item in shop_plan["items"][:3]]
    top_str = ", ".join(top_items)

    if days_until <= 0:
        shopping_reminder = ("error", f"⚠️ Go shopping today — running short on {top_str}")
    elif days_until == 1:
        shopping_reminder = ("warning", f"🛒 Shop tomorrow before you run out of {top_str}")
    else:
        shopping_reminder = ("info", f"🗓️ Plan to shop by {shop_by.strftime('%A')} — {len(shop_plan['items'])} item(s) needed")

has_ahead = thaw_reminders or shopping_reminder
if has_ahead:
    st.divider()
    st.markdown("## What to Do Today")

    for reminder in thaw_reminders:
        st.info(reminder)

    if shopping_reminder:
        level, msg = shopping_reminder
        if level == "error":
            st.error(msg)
        elif level == "warning":
            st.warning(msg)
        else:
            st.info(msg)

# ---------------------------------------------------------------------------
# Section 3: Plan For (the week ahead)
# ---------------------------------------------------------------------------
st.divider()
st.markdown("## This Week")

# Compact 7-day week view
h_date, h_b, h_l, h_d = st.columns([1.5, 2.5, 2.5, 2.5])
with h_date:
    st.markdown("**Date**")
with h_b:
    st.markdown("**🌅 Breakfast**")
with h_l:
    st.markdown("**☀️ Lunch**")
with h_d:
    st.markdown("**🌙 Dinner**")

week_entries = get_meal_entries(today.isoformat(), (today + timedelta(days=6)).isoformat())

for i in range(7):
    d = today + timedelta(days=i)
    day_meals = week_entries.get(d.isoformat(), {})
    is_today = i == 0

    col_date, col_b, col_l, col_d = st.columns([1.5, 2.5, 2.5, 2.5])

    day_label = "Today" if is_today else d.strftime("%a %b %-d")

    with col_date:
        if is_today:
            st.markdown(f"**{day_label}**")
        else:
            st.write(day_label)

    for col, mt in zip([col_b, col_l, col_d], ["Breakfast", "Lunch", "Dinner"]):
        meal = day_meals.get(mt, UNPLANNED)
        with col:
            if meal == UNPLANNED:
                st.caption("—")
            elif is_today:
                st.markdown(f"**{meal}**")
            else:
                st.write(meal)

# Pantry alerts
st.write("")
forgotten = get_forgotten_ingredients()
if forgotten:
    forgotten_names = ", ".join(i["name"] for i in forgotten)
    st.warning(f"⚠️ **{forgotten_names}** aren't used in any saved recipe")
else:
    st.success("✅ All pantry items are used in at least one recipe")

# Shopping coverage (positive signal if fully covered)
if shop_plan and shop_plan["fully_covered"]:
    st.success("✅ Your pantry covers all planned meals this week")

# ---------------------------------------------------------------------------
# Cooking stats (collapsed)
# ---------------------------------------------------------------------------
st.divider()
with st.expander("📊 Cooking Stats"):
    stat_col1, stat_col2 = st.columns(2)

    with stat_col1:
        st.subheader("🍳 Most Cooked Recipes")
        most_cooked = get_most_cooked_recipes()
        if not most_cooked:
            st.info("No cooking history yet.")
            st.page_link("pages/2_Recipes.py", label="Mark a recipe as cooked →")
        else:
            for item in most_cooked:
                st.write(f"**{item['name']}** — cooked {item['count']} time(s)")

    with stat_col2:
        st.subheader("🥕 Most Used Ingredients")
        most_used = get_most_used_ingredients()
        if not most_used:
            st.info("No cooking history yet.")
        else:
            for item in most_used:
                st.write(f"**{item['name']}** — used {item['count']} time(s)")

    st.page_link("pages/3_Suggestions.py", label="See what you can cook now →")

# ---------------------------------------------------------------------------
# AI Insight (singular, below main sections)
# ---------------------------------------------------------------------------
st.divider()
st.subheader("💡 AI Insight")

if "home_insight" not in st.session_state:
    if not ingredients:
        st.session_state["home_insight"] = "Add some ingredients to your fridge to get personalised insights."
    elif not recipes:
        st.session_state["home_insight"] = "Add some recipes to get personalised insights based on your fridge."
    else:
        with st.spinner("Generating insight based on your fridge..."):
            try:
                cookable = get_cookable_recipes()
                forgotten = get_forgotten_ingredients()
                st.session_state["home_insight"] = generate_home_insight(
                    ingredients, recipes, cookable, forgotten
                )
            except Exception as e:
                st.session_state["home_insight"] = f"Could not generate insight: {e}"

st.markdown(st.session_state["home_insight"])

if st.button("Refresh Insight"):
    del st.session_state["home_insight"]
    st.rerun()
