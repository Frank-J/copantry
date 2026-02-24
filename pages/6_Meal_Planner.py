import streamlit as st
from datetime import date, timedelta
from database import initialize_db, get_recipes, get_shopping_plan, get_meal_entries, save_meal_entry
from gemini_client import suggest_calendar_meals
from utils import apply_sidebar_style

initialize_db()

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

    # Always start from today, show next 7 days per "week"
    today = date.today()
    week_start = today + timedelta(weeks=st.session_state["week_offset"])
    week_dates = [week_start + timedelta(days=i) for i in range(7)]

    # Week label
    offset = st.session_state["week_offset"]
    week_label = f"{week_dates[0].strftime('%b %d')} – {week_dates[6].strftime('%b %d, %Y')}"
    if offset == 0:
        week_label += " · Next 7 Days"
    elif offset > 0:
        week_label += f" · +{offset} Week{'s' if offset > 1 else ''}"
    else:
        week_label += f" · {abs(offset)} Week{'s' if abs(offset) > 1 else ''} Ago"

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
    MEAL_TYPES = ["Breakfast", "Lunch", "Dinner"]

    recipe_names = [r["name"] for r in recipes]
    all_options = SPECIAL + recipe_names

    # Load from DB on page open (only fill keys not already in session state)
    db_entries = get_meal_entries(week_dates[0].isoformat(), week_dates[-1].isoformat())
    for d in week_dates:
        day_meals = db_entries.get(d.isoformat(), {})
        for meal_type in MEAL_TYPES:
            sk = f"meal_{d.isoformat()}_{meal_type}"
            if sk not in st.session_state:
                st.session_state[sk] = day_meals.get(meal_type, UNPLANNED)

    def _save_meal(date_key, meal_type):
        val = st.session_state.get(f"meal_{date_key}_{meal_type}", UNPLANNED)
        save_meal_entry(date_key, meal_type, val)

    day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    # Table header row
    h_day, h_breakfast, h_lunch, h_dinner = st.columns([1.5, 2.5, 2.5, 2.5])
    with h_day:
        st.markdown("**Day**")
    with h_breakfast:
        st.markdown("**🌅 Breakfast**")
    with h_lunch:
        st.markdown("**☀️ Lunch**")
    with h_dinner:
        st.markdown("**🌙 Dinner**")

    for day_date, day_label in zip(week_dates, day_labels):
        date_key = day_date.isoformat()
        is_today = day_date == today

        col_day, col_breakfast, col_lunch, col_dinner = st.columns([1.5, 2.5, 2.5, 2.5])

        with col_day:
            label = f"**{day_label} {day_date.strftime('%b %d')}**" if is_today else f"{day_label} {day_date.strftime('%b %d')}"
            if is_today:
                st.markdown(f"{label} 🔵")
            else:
                st.markdown(label)

        for col, meal_type in zip([col_breakfast, col_lunch, col_dinner], MEAL_TYPES):
            with col:
                sk = f"meal_{date_key}_{meal_type}"
                current = st.session_state.get(sk, UNPLANNED)
                if current not in all_options:
                    current = UNPLANNED
                    st.session_state[sk] = current
                st.selectbox(
                    f"{meal_type} for {date_key}",
                    all_options,
                    index=all_options.index(current),
                    key=sk,
                    label_visibility="collapsed",
                    on_change=_save_meal,
                    args=(date_key, meal_type),
                )

    st.divider()

    # Week summary
    all_week_values = {
        (d.isoformat(), mt): st.session_state.get(f"meal_{d.isoformat()}_{mt}", UNPLANNED)
        for d in week_dates
        for mt in MEAL_TYPES
    }

    home_count = sum(1 for v in all_week_values.values() if v not in SPECIAL)
    eating_out_count = sum(1 for v in all_week_values.values() if v == EATING_OUT)
    vacation_count = sum(1 for v in all_week_values.values() if v == VACATION)
    unplanned_count = sum(1 for v in all_week_values.values() if v == UNPLANNED)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Home Meals", home_count)
    c2.metric("Eating Out", eating_out_count)
    c3.metric("Vacation / Skip", vacation_count)
    c4.metric("Unplanned", unplanned_count)

    st.divider()

    # Build flat meal plan {date_str: recipe_name} for functions that expect it
    # Use dinner as primary for AI suggestions (backward compat), but pass all meals for shopping
    home_meals_flat = {}
    for (date_str, mt), val in all_week_values.items():
        if val not in SPECIAL:
            # Use date+mealtype combo key for shopping plan
            home_meals_flat[f"{date_str}_{mt}"] = val

    # For AI suggestions we still use a per-day map (dinner preferred, else first home meal found)
    day_primary_map = {}
    for d in week_dates:
        date_str = d.isoformat()
        for mt in MEAL_TYPES:
            val = st.session_state.get(f"meal_{date_str}_{mt}", UNPLANNED)
            if val not in SPECIAL:
                day_primary_map[date_str] = val
                break

    # Action buttons
    col_ai, col_shop = st.columns(2)

    with col_ai:
        if st.button("✨ Fill Unplanned Days with AI", use_container_width=True):
            # Find days where ALL meal slots are unplanned
            unplanned_dates = []
            for d in week_dates:
                date_str = d.isoformat()
                all_unplanned = all(
                    st.session_state.get(f"meal_{date_str}_{mt}", UNPLANNED) == UNPLANNED
                    for mt in MEAL_TYPES
                )
                if all_unplanned:
                    unplanned_dates.append(date_str)

            if not unplanned_dates:
                st.info("No fully unplanned days — all days have at least one meal or status assigned.")
            else:
                with st.spinner("Suggesting meals for unplanned days..."):
                    try:
                        suggestions = suggest_calendar_meals(recipes, unplanned_dates, day_primary_map)
                        for date_str, recipe_name in suggestions.items():
                            if recipe_name in recipe_names:
                                sk = f"meal_{date_str}_Dinner"
                                st.session_state[sk] = recipe_name
                                save_meal_entry(date_str, "Dinner", recipe_name)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not suggest meals: {e}")

    with col_shop:
        if st.button("🛒 Shopping Plan", use_container_width=True, type="primary"):
            if not home_meals_flat:
                st.warning("No home meals planned yet — add some recipes to the calendar first.")
            else:
                plan = get_shopping_plan(home_meals_flat, recipes)
                st.session_state["shopping_plan"] = plan

    if "shopping_plan" in st.session_state:
        plan = st.session_state["shopping_plan"]
        st.divider()

        if plan["fully_covered"]:
            st.success("✅ Your pantry has everything needed for all planned meals.")
        else:
            shop_by_date = date.fromisoformat(plan["shop_by"])
            st.error(f"🛒 **Shop by {shop_by_date.strftime('%A, %b %d')}** — you'll start running short after that.")

            # Build display table
            rows = []
            for item in plan["items"]:
                rows.append({
                    "Ingredient": item["name"],
                    "Need": f"{item['need_amount']} {item['need_unit']}",
                    "Have": f"{item['have_amount']} {item['have_unit']}",
                    "Runs out": date.fromisoformat(item["runs_out_on"]).strftime("%a %b %d"),
                    "For recipe": item["recipe"],
                })

            st.markdown("**What to buy:**")
            st.table(rows)

            # Plain-text download
            lines = [
                f"Shopping Plan — shop by {shop_by_date.strftime('%A, %b %d')}",
                "",
            ]
            for item in plan["items"]:
                lines.append(
                    f"- {item['name']}: need {item['need_amount']} {item['need_unit']} "
                    f"(have {item['have_amount']} {item['have_unit']}) "
                    f"— runs out {date.fromisoformat(item['runs_out_on']).strftime('%a %b %d')} "
                    f"for {item['recipe']}"
                )
            st.download_button(
                label="Download Shopping Plan",
                data="\n".join(lines),
                file_name="shopping_plan.txt",
                mime="text/plain",
                use_container_width=True,
            )
