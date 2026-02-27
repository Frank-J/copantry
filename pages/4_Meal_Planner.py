import streamlit as st
from datetime import date, timedelta
from database import (
    initialize_db,
    get_recipes,
    get_ingredients,
    get_recipe_cook_counts,
    get_meal_entries,
    save_meal_entry,
    get_shopping_plan,
)
from gemini_client import suggest_calendar_meals, reschedule_around_grocery_date
from utils import apply_sidebar_style, get_local_date
from streamlit_js_eval import streamlit_js_eval

initialize_db()

st.set_page_config(page_title="CoPantry · Meal Planner", page_icon="📅", layout="wide")
apply_sidebar_style()

tz_offset = streamlit_js_eval(js_expressions="new Date().getTimezoneOffset()", key="tz_offset")
if tz_offset is None:
    st.stop()

st.title("📅 Meal Planner")
st.markdown("Plan your meals for the week. Changes are saved automatically.")

st.divider()

recipes = get_recipes()

if not recipes:
    st.warning("No saved recipes yet — add some recipes to start planning.")
    st.page_link("pages/2_Recipes.py", label="Add a Recipe →")
else:
    # Sort recipes by most-cooked so frequent meals appear first
    cook_counts = get_recipe_cook_counts()
    recipes_sorted = sorted(recipes, key=lambda r: cook_counts.get(r["name"], 0), reverse=True)

    # Week navigation state
    if "week_offset" not in st.session_state:
        st.session_state["week_offset"] = 0

    today = get_local_date(tz_offset)
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
    GROCERY_ITEM_THRESHOLD = 5

    recipe_names = [r["name"] for r in recipes_sorted]
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

    # Table header
    h_day, h_breakfast, h_lunch, h_dinner = st.columns([1.5, 2.5, 2.5, 2.5])
    with h_day:
        st.markdown("**Day**")
    with h_breakfast:
        st.markdown("**🌅 Breakfast**")
    with h_lunch:
        st.markdown("**☀️ Lunch**")
    with h_dinner:
        st.markdown("**🌙 Dinner**")

    st.caption("Tip: type in a dropdown to search recipes")

    # Compute grocery day to annotate the calendar
    home_meals_flat = {}
    for d in week_dates:
        for mt in MEAL_TYPES:
            val = st.session_state.get(f"meal_{d.isoformat()}_{mt}", UNPLANNED)
            if val not in SPECIAL:
                home_meals_flat[f"{d.isoformat()}_{mt}"] = val

    shop_by_date = None
    if home_meals_flat:
        plan = get_shopping_plan(home_meals_flat, recipes)
        if not plan["fully_covered"] and len(plan["items"]) >= GROCERY_ITEM_THRESHOLD:
            shop_by_date = date.fromisoformat(plan["shop_by"])

    # Calendar rows
    for day_date, day_label in zip(week_dates, day_labels):
        date_key = day_date.isoformat()
        is_today = day_date == today
        is_shop_day = shop_by_date and day_date == shop_by_date

        col_day, col_breakfast, col_lunch, col_dinner = st.columns([1.5, 2.5, 2.5, 2.5])

        with col_day:
            label_text = f"{day_label} {day_date.strftime('%b %-d')}"
            badges = ""
            if is_today:
                badges += " 🔵"
            if is_shop_day:
                badges += " 🛒"
            if is_today:
                st.markdown(f"**{label_text}**{badges}")
            else:
                st.markdown(f"{label_text}{badges}")

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

    # Week summary metrics
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

    # ---------------------------------------------------------------------------
    # Grocery recommendation
    # ---------------------------------------------------------------------------
    if home_meals_flat:
        plan = get_shopping_plan(home_meals_flat, recipes)
        item_count = len(plan["items"])

        if plan["fully_covered"]:
            st.divider()
            st.success("✅ Your pantry covers all planned meals this week — no shopping trip needed.")

        elif item_count < GROCERY_ITEM_THRESHOLD:
            st.divider()
            st.info(
                f"🛒 You're short on {item_count} item(s) this week — not enough to warrant a dedicated trip. "
                f"Check your Shopping List for details."
            )
            st.page_link("pages/5_Shopping_List.py", label="View Shopping List →")

        else:
            st.divider()
            shop_by = date.fromisoformat(plan["shop_by"])
            days_until = (shop_by - today).days

            if days_until <= 0:
                st.error(
                    f"⚠️ We recommend an urgent grocery run today — you need {item_count} items "
                    f"and your meal plan is already at risk."
                )
            elif days_until == 1:
                st.warning(
                    f"🛒 We recommend a grocery run **tomorrow, {shop_by.strftime('%A %b %-d')}** "
                    f"— {item_count} items to keep your meal plan on track."
                )
            else:
                st.info(
                    f"🛒 We recommend a grocery run by **{shop_by.strftime('%A, %b %-d')}** "
                    f"— {item_count} items to keep your meal plan on track."
                )

            with st.expander("See what to buy"):
                for item in plan["items"]:
                    st.write(
                        f"- **{item['name']}** — {item['need_amount']} {item['need_unit']} "
                        f"(have {item['have_amount']} {item['have_unit']}) for *{item['recipe']}*"
                    )

            # Can't make it flow
            st.markdown("**Can't make it by then?**")
            col_date, col_btn = st.columns([3, 1])
            with col_date:
                alt_date = st.date_input(
                    "When can you shop?",
                    min_value=today + timedelta(days=1),
                    key="alt_grocery_date",
                    label_visibility="collapsed",
                )
            with col_btn:
                reschedule_clicked = st.button(
                    "✨ Reschedule with AI",
                    use_container_width=True,
                    key="reschedule_btn",
                )

            if reschedule_clicked:
                current_meal_plan = {}
                for d in week_dates:
                    date_str = d.isoformat()
                    day_meals = {}
                    for mt in MEAL_TYPES:
                        val = st.session_state.get(f"meal_{date_str}_{mt}", UNPLANNED)
                        if val != UNPLANNED:
                            day_meals[mt] = val
                    if day_meals:
                        current_meal_plan[date_str] = day_meals

                pantry = get_ingredients()
                with st.spinner("Reworking your meal plan around your grocery date..."):
                    try:
                        result = reschedule_around_grocery_date(
                            current_meal_plan,
                            recipes,
                            pantry,
                            alt_date.isoformat(),
                        )
                        new_plan = result.get("plan", {})
                        feasible = result.get("feasible", True)
                        note = result.get("note", "")

                        # Apply new plan to session state and DB
                        for date_str, meals in new_plan.items():
                            for mt, meal_name in meals.items():
                                if meal_name in all_options:
                                    sk = f"meal_{date_str}_{mt}"
                                    st.session_state[sk] = meal_name
                                    save_meal_entry(date_str, mt, meal_name)

                        if not feasible:
                            st.error(
                                f"⚠️ {note}\n\nSome meals before your grocery date couldn't be covered "
                                f"from your current pantry. Consider urgently picking up a few essentials: "
                                f"{', '.join(item['name'] for item in plan['items'][:5])}."
                            )
                        else:
                            if note:
                                st.success(f"✅ Meal plan rescheduled. {note}")
                            else:
                                st.success("✅ Meal plan rescheduled around your grocery date.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not reschedule: {e}")

    st.divider()

    # Action buttons
    # For AI suggestions use a per-day map (dinner preferred, else first home meal found)
    day_primary_map = {}
    for d in week_dates:
        date_str = d.isoformat()
        for mt in MEAL_TYPES:
            val = st.session_state.get(f"meal_{date_str}_{mt}", UNPLANNED)
            if val not in SPECIAL:
                day_primary_map[date_str] = val
                break

    col_ai, col_shop = st.columns(2)

    with col_ai:
        if st.button("✨ Fill Unplanned Days with AI", use_container_width=True):
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
        st.page_link("pages/5_Shopping_List.py", label="🛒 View Shopping List →")
