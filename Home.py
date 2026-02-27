import streamlit as st
from datetime import date, timedelta
from utils import apply_sidebar_style, get_local_date
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
    save_meal_entry,
)

initialize_db()
from gemini_client import generate_home_insight

st.set_page_config(page_title="CoPantry · Home", page_icon="🏠", layout="wide")
apply_sidebar_style()

st.title("🏠 Home")

# ---------------------------------------------------------------------------
# Load shared data
# ---------------------------------------------------------------------------
if "date_override" not in st.session_state:
    st.session_state["date_override"] = get_local_date()
today = st.session_state["date_override"]

ingredients = get_ingredients()
recipes = get_recipes()
recipe_map = {r["name"]: r for r in recipes}

# ---------------------------------------------------------------------------
# Section 1: Today
# ---------------------------------------------------------------------------
day_name = today.strftime("%A")
date_label = today.strftime("%B %-d")
st.markdown(f"## Today — {day_name}, {date_label}")

col_picker, col_caption = st.columns([1.5, 5])
with col_picker:
    new_date = st.date_input("date", value=today, label_visibility="collapsed", key="date_picker")
    if new_date != today:
        st.session_state["date_override"] = new_date
        st.rerun()
with col_caption:
    st.caption("App uses UTC — adjust the date if today looks off.")

today_meals = get_meals_for_date(today.isoformat())

UNPLANNED = "— Unplanned —"
EATING_OUT = "🍽️ Eating Out"
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
        if meal != EATING_OUT:
            if st.button("🍽️ Eating Out", key=f"eo_{meal_type}", use_container_width=True, type="secondary"):
                st.session_state[f"prev_meal_{meal_type}"] = meal
                save_meal_entry(today.isoformat(), meal_type, EATING_OUT)
                st.rerun()
        else:
            if st.button("↩️ Undo", key=f"undo_{meal_type}", use_container_width=True, type="secondary"):
                prev = st.session_state.get(f"prev_meal_{meal_type}", UNPLANNED)
                save_meal_entry(today.isoformat(), meal_type, prev)
                st.rerun()

all_unplanned_today = all(v == UNPLANNED for v in today_meals.values())
if all_unplanned_today:
    st.caption("Nothing planned yet. [Go to Meal Planner →](pages/4_Meal_Planner)")

# ---------------------------------------------------------------------------
# Section 2: Ahead of Time (prep reminders)
# ---------------------------------------------------------------------------

def _ing(text):
    """Highlight an ingredient name in dark blue."""
    return f'<span style="font-weight:700;color:#1a56db;">{text}</span>'

def _dt(text):
    """Highlight a date in dark orange."""
    return f'<span style="font-weight:700;color:#9a3412;">{text}</span>'

def _callout(level, html):
    """Render a styled callout box with HTML content."""
    styles = {
        "info":    ("#eff6ff", "#3b82f6"),
        "warning": ("#fffbeb", "#f59e0b"),
        "error":   ("#fef2f2", "#ef4444"),
    }
    bg, border = styles[level]
    st.markdown(
        f'<div style="background:{bg};border-left:4px solid {border};color:#1f2937;'
        f'padding:12px 16px;border-radius:4px;margin-bottom:8px;line-height:1.7;">'
        f'{html}</div>',
        unsafe_allow_html=True,
    )

thaw_reminders = []

# Build freezer ingredient map from pantry
freezer_items = {i["name"].lower(): i["name"] for i in ingredients if (i.get("location") or "Fridge") == "Freezer"}

if freezer_items and recipes:
    # Check tomorrow and day after for planned meals needing frozen ingredients
    for days_ahead in [1, 2]:
        check_date = today + timedelta(days=days_ahead)
        check_meals = get_meals_for_date(check_date.isoformat())
        check_date_label = check_date.strftime("%A, %b %-d")

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
                            f"❄️ Take {_ing(display_name)} out of the freezer today — needed for {meal_name} tomorrow ({_dt(check_date_label)})"
                        )
                    else:
                        thaw_reminders.append(
                            f"❄️ Take {_ing(display_name)} out tomorrow — needed for {meal_name} on {_dt(check_date_label)}"
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
    top_str = ", ".join(_ing(name) for name in top_items)
    today_label = _dt(f"today, {today.strftime('%A, %b %-d')}")
    tomorrow_label = _dt(f"tomorrow, {(today + timedelta(days=1)).strftime('%A, %b %-d')}")

    if days_until <= 0:
        shopping_reminder = ("error", f"⚠️ Go shopping {today_label} — running short on {top_str}")
    elif days_until == 1:
        shopping_reminder = ("warning", f"🛒 Shop {tomorrow_label} before you run out of {top_str}")
    else:
        shopping_reminder = ("info", f"🗓️ Plan to shop by {_dt(shop_by.strftime('%A, %b %-d'))} — {len(shop_plan['items'])} item(s) needed")

has_ahead = thaw_reminders or shopping_reminder
if has_ahead:
    st.divider()
    st.markdown("## What to Do Today")

    for reminder in thaw_reminders:
        _callout("info", reminder)

    if shopping_reminder:
        level, msg = shopping_reminder
        _callout(level, msg)

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

