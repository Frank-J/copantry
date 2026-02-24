import streamlit as st
from datetime import date, timedelta
from database import get_recipes, get_ingredients
from gemini_client import suggest_calendar_meals, generate_weekly_shopping_list
from utils import apply_sidebar_style

st.set_page_config(page_title="Meal Planner", page_icon="📅", layout="wide")
apply_sidebar_style()

st.title("📅 Meal Planner")
st.markdown("Plan your meals for the week, then generate a shopping list for what you need.")

st.divider()

recipes = get_recipes()

if not recipes:
    st.warning("No saved recipes yet — add some recipes to start planning.")
    st.page_link("pages/4_Recipes.py", label="Add a Recipe →")
else:
    # Week navigation state
    if "week_offset" not in st.session_state:
        st.session_state["week_offset"] = 0

    # Calculate current week (Mon–Sun)
    today = date.today()
    week_start = today - timedelta(days=today.weekday()) + timedelta(weeks=st.session_state["week_offset"])
    week_dates = [week_start + timedelta(days=i) for i in range(7)]

    # Week label
    offset = st.session_state["week_offset"]
    week_label = f"{week_dates[0].strftime('%b %d')} – {week_dates[6].strftime('%b %d, %Y')}"
    if offset == 0:
        week_label += " · This Week"
    elif offset == 1:
        week_label += " · Next Week"
    elif offset == -1:
        week_label += " · Last Week"

    col_prev, col_title, col_next = st.columns([1, 5, 1])
    with col_prev:
        if st.button("← Prev", use_container_width=True):
            st.session_state["week_offset"] -= 1
            st.rerun()
    with col_title:
        st.markdown(f"### {week_label}")
    with col_next:
        if st.button("Next →", use_container_width=True):
            st.session_state["week_offset"] += 1
            st.rerun()

    # Day option constants
    UNPLANNED = "— Unplanned —"
    EATING_OUT = "🍽️ Eating Out"
    VACATION = "🏖️ Vacation / Skip"
    SPECIAL = [UNPLANNED, EATING_OUT, VACATION]

    recipe_names = [r["name"] for r in recipes]
    all_options = SPECIAL + recipe_names

    day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    def render_day(col, day_date, day_label):
        date_key = day_date.isoformat()
        sk = f"meal_{date_key}"
        is_today = day_date == today
        with col:
            if is_today:
                st.markdown(f"**{day_label} · {day_date.strftime('%b %d')}** 🔵")
            else:
                st.markdown(f"**{day_label} · {day_date.strftime('%b %d')}**")
            if sk not in st.session_state:
                st.session_state[sk] = UNPLANNED
            current = st.session_state[sk]
            if current not in all_options:
                current = UNPLANNED
            st.selectbox(
                "Meal",
                all_options,
                index=all_options.index(current),
                key=sk,
                label_visibility="collapsed",
            )

    # Row 1: Mon–Thu
    row1 = st.columns(4)
    for col, day_date, day_label in zip(row1, week_dates[:4], day_labels[:4]):
        render_day(col, day_date, day_label)

    st.write("")

    # Row 2: Fri–Sun (3 days, padded with an empty column to keep consistent width)
    row2 = st.columns(4)
    for col, day_date, day_label in zip(row2, week_dates[4:], day_labels[4:]):
        render_day(col, day_date, day_label)

    st.divider()

    # Week summary
    week_values = {
        d.isoformat(): st.session_state.get(f"meal_{d.isoformat()}", UNPLANNED)
        for d in week_dates
    }

    home_count = sum(1 for v in week_values.values() if v not in SPECIAL)
    eating_out_count = sum(1 for v in week_values.values() if v == EATING_OUT)
    vacation_count = sum(1 for v in week_values.values() if v == VACATION)
    unplanned_count = sum(1 for v in week_values.values() if v == UNPLANNED)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Home Meals", home_count)
    c2.metric("Eating Out", eating_out_count)
    c3.metric("Vacation / Skip", vacation_count)
    c4.metric("Unplanned", unplanned_count)

    st.divider()

    # Action buttons
    col_ai, col_shop = st.columns(2)

    with col_ai:
        if st.button("✨ Fill Unplanned Days with AI", use_container_width=True):
            unplanned_dates = [
                d.isoformat() for d in week_dates if week_values[d.isoformat()] == UNPLANNED
            ]
            if not unplanned_dates:
                st.info("No unplanned days — all days already have a meal or status assigned.")
            else:
                with st.spinner("Suggesting meals for unplanned days..."):
                    try:
                        suggestions = suggest_calendar_meals(recipes, unplanned_dates, week_values)
                        for date_str, recipe_name in suggestions.items():
                            if recipe_name in recipe_names:
                                st.session_state[f"meal_{date_str}"] = recipe_name
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not suggest meals: {e}")

    with col_shop:
        if st.button("🛒 Generate Weekly Shopping List", use_container_width=True, type="primary"):
            home_meals = {d: v for d, v in week_values.items() if v not in SPECIAL}
            if not home_meals:
                st.warning("No home meals planned yet — add some recipes to the calendar first.")
            else:
                fridge = get_ingredients()
                with st.spinner("Building your shopping list..."):
                    try:
                        planned_recipes = [r for r in recipes if r["name"] in home_meals.values()]
                        result = generate_weekly_shopping_list(home_meals, planned_recipes, fridge)
                        st.session_state["weekly_shopping_list"] = result
                    except Exception as e:
                        st.error(f"Could not generate shopping list: {e}")

    if "weekly_shopping_list" in st.session_state:
        st.divider()
        st.subheader("🛒 Weekly Shopping List")
        st.markdown(st.session_state["weekly_shopping_list"])
        st.download_button(
            label="Download Shopping List",
            data=st.session_state["weekly_shopping_list"],
            file_name="weekly_shopping_list.txt",
            mime="text/plain",
            use_container_width=True,
        )
