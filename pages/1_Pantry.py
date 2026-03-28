import streamlit as st
from datetime import datetime, date
from database import initialize_db, get_ingredients, get_ingredient_by_name, add_ingredient, delete_ingredient, update_ingredient, clear_all_ingredients, check_and_increment_quota
from constants import UNITS, AI_DAILY_LIMIT
from utils import apply_sidebar_style, show_ai_limit_message
from gemini_client import suggest_storage_locations_bulk

initialize_db()

st.set_page_config(page_title="CoPantry · Pantry", page_icon="🥫", layout="wide")
apply_sidebar_style()

st.markdown("""
<style>
button[data-testid^="stBaseButton-secondary"],
button[data-testid^="stBaseButton-primary"] {
    padding-top: 1px !important;
    padding-bottom: 1px !important;
    min-height: 28px !important;
    line-height: 1.2 !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🥫 My Pantry")
st.markdown("Track all the ingredients you have at home — fridge, freezer, and pantry.")

st.divider()

LOCATIONS = ["Fridge", "Freezer", "Pantry", "Other"]
LOCATION_ICONS = {"Fridge": "🧊", "Freezer": "❄️", "Pantry": "🥫", "Other": "📦"}

# ---------------------------------------------------------------------------
# Add ingredients — multi-row, no form, session-state driven
# ---------------------------------------------------------------------------
st.subheader("Add Ingredients")

# Initialise row tracking
if "add_row_ids" not in st.session_state:
    st.session_state["add_row_ids"] = [0]
    st.session_state["add_row_counter"] = 1

row_ids = st.session_state["add_row_ids"]

# Column headers
h1, h2, h3, h4, h5, h6 = st.columns([2.5, 1.2, 1.5, 1.5, 1.8, 0.5])
with h1: st.caption("**Ingredient**")
with h2: st.caption("**Amount**")
with h3: st.caption("**Unit**")
with h4: st.caption("**Location**")
with h5: st.caption("**Expiry (optional)**")

for rid in list(row_ids):
    col_name, col_amount, col_unit, col_location, col_expiry, col_remove = st.columns([2.5, 1.2, 1.5, 1.5, 1.8, 0.5])

    with col_name:
        st.text_input("Name", key=f"r_name_{rid}", placeholder="e.g. Eggs",
                      label_visibility="collapsed")
    with col_amount:
        st.number_input("Amount", key=f"r_amount_{rid}", min_value=0.1, value=1.0, step=0.5,
                        label_visibility="collapsed")
    with col_unit:
        st.selectbox("Unit", UNITS, key=f"r_unit_{rid}", label_visibility="collapsed")
    with col_location:
        # Apply any pending location suggestion before the widget renders
        if f"r_location_pending_{rid}" in st.session_state:
            st.session_state[f"r_location_{rid}"] = st.session_state.pop(f"r_location_pending_{rid}")
        st.selectbox("Location", LOCATIONS, key=f"r_location_{rid}", label_visibility="collapsed")
    with col_expiry:
        st.date_input("Expiry", value=None, key=f"r_expiry_{rid}", label_visibility="collapsed")
    with col_remove:
        if len(row_ids) > 1 and st.button("✕", key=f"r_remove_{rid}"):
            st.session_state["add_row_ids"].remove(rid)
            for field in ["name", "amount", "unit", "location", "tip", "location_pending"]:
                st.session_state.pop(f"r_{field}_{rid}", None)
            st.rerun()

    tip = st.session_state.get(f"r_tip_{rid}")
    if tip:
        st.markdown(
            f'<div style="margin-top:-10px;margin-bottom:4px;color:#6b7280;font-size:0.85em;">ℹ️ {tip}</div>',
            unsafe_allow_html=True,
        )

def _clear_add_rows():
    for rid in st.session_state.get("add_row_ids", []):
        for field in ["name", "amount", "unit", "location", "tip", "location_pending", "expiry"]:
            st.session_state.pop(f"r_{field}_{rid}", None)
    st.session_state["add_row_ids"] = [0]
    st.session_state["add_row_counter"] = 1


@st.dialog("Duplicate Ingredients Found")
def confirm_duplicates():
    conflicts = st.session_state.get("pending_conflicts", [])
    clean_rows = st.session_state.get("pending_clean_rows", [])

    st.write("The following ingredient(s) already exist in your pantry:")
    for c in conflicts:
        existing, new = c["existing"], c["new"]
        if existing["unit"] == new["unit"]:
            total = existing["amount"] + new["amount"]
            st.markdown(
                f"**{existing['name']}** — currently {existing['amount']} {existing['unit']}, "
                f"adding {new['amount']} {new['unit']} → **{total} {existing['unit']}** total"
            )
        else:
            st.markdown(
                f"**{existing['name']}** — currently {existing['amount']} {existing['unit']}, "
                f"adding {new['amount']} {new['unit']} *(different units — will be added as a separate entry)*"
            )

    st.write("")
    col_combine, col_separate = st.columns(2)
    with col_combine:
        if st.button("Combine amounts", type="primary", width="stretch"):
            saved = []
            for row in clean_rows:
                add_ingredient(row["name"], row["amount"], row["unit"], row["location"], row.get("expiry_date"))
                saved.append(row["name"])
            for c in conflicts:
                existing, new = c["existing"], c["new"]
                if existing["unit"] == new["unit"]:
                    update_ingredient(existing["id"], existing["amount"] + new["amount"], new["location"])
                else:
                    add_ingredient(new["name"], new["amount"], new["unit"], new["location"])
                saved.append(existing["name"])
            for key in ["pending_clean_rows", "pending_conflicts"]:
                st.session_state.pop(key, None)
            _clear_add_rows()
            st.session_state["add_success"] = f"Saved: {', '.join(saved)}"
            st.rerun(scope="app")
    with col_separate:
        if st.button("Add as separate entries", width="stretch"):
            saved = []
            for row in clean_rows + [c["new"] for c in conflicts]:
                add_ingredient(row["name"], row["amount"], row["unit"], row["location"], row.get("expiry_date"))
                saved.append(row["name"])
            for key in ["pending_clean_rows", "pending_conflicts"]:
                st.session_state.pop(key, None)
            _clear_add_rows()
            st.session_state["add_success"] = f"Added: {', '.join(saved)}"
            st.rerun(scope="app")


# Action row
btn_add_row, btn_suggest, btn_save, _ = st.columns([1.5, 2, 1.5, 4])
with btn_add_row:
    if st.button("+ Add row", width="stretch"):
        new_id = st.session_state["add_row_counter"]
        st.session_state["add_row_ids"].append(new_id)
        st.session_state["add_row_counter"] += 1
        st.rerun()
with btn_suggest:
    if st.button("💡 Suggest Locations", width="stretch"):
        named_rows = [(rid, st.session_state.get(f"r_name_{rid}", "").strip())
                      for rid in row_ids
                      if st.session_state.get(f"r_name_{rid}", "").strip()]
        if not named_rows:
            st.toast("Enter at least one ingredient name first.", icon="⚠️")
        elif not check_and_increment_quota(AI_DAILY_LIMIT):
            show_ai_limit_message()
        else:
            with st.spinner("Getting storage suggestions..."):
                try:
                    results = suggest_storage_locations_bulk([n for _, n in named_rows])
                    for rid, name in named_rows:
                        suggestion = results.get(name, {})
                        if suggestion.get("location") in LOCATIONS:
                            st.session_state[f"r_location_pending_{rid}"] = suggestion["location"]
                        if suggestion.get("tip"):
                            st.session_state[f"r_tip_{rid}"] = suggestion["tip"]
                    st.rerun()
                except Exception as e:
                    st.toast(f"Could not get suggestions: {e}", icon="⚠️")
with btn_save:
    if st.button("Save to Pantry", type="primary", width="stretch"):
        rows_to_save = []
        for rid in st.session_state["add_row_ids"]:
            name = st.session_state.get(f"r_name_{rid}", "").strip()
            if not name:
                continue
            expiry = st.session_state.get(f"r_expiry_{rid}")
            rows_to_save.append({
                "name": name,
                "amount": st.session_state.get(f"r_amount_{rid}", 1.0),
                "unit": st.session_state.get(f"r_unit_{rid}", "whole"),
                "location": st.session_state.get(f"r_location_{rid}", "Fridge"),
                "expiry_date": expiry.isoformat() if expiry else None,
            })

        if not rows_to_save:
            st.error("Please enter at least one ingredient name.")
        else:
            conflicts, clean_rows = [], []
            for row in rows_to_save:
                existing = get_ingredient_by_name(row["name"])
                if existing:
                    conflicts.append({"existing": existing, "new": row})
                else:
                    clean_rows.append(row)

            if conflicts:
                st.session_state["pending_clean_rows"] = clean_rows
                st.session_state["pending_conflicts"] = conflicts
                confirm_duplicates()
            else:
                for row in clean_rows:
                    add_ingredient(row["name"], row["amount"], row["unit"], row["location"], row.get("expiry_date"))
                _clear_add_rows()
                st.session_state["add_success"] = f"Added: {', '.join(r['name'] for r in clean_rows)}"
                st.rerun()

if "add_success" in st.session_state:
    st.success(f"✅ {st.session_state.pop('add_success')}")

st.divider()


# ---------------------------------------------------------------------------
# Clear all dialog
# ---------------------------------------------------------------------------
@st.dialog("Clear All Ingredients")
def confirm_clear_pantry():
    st.warning("⚠️ This will permanently delete **all ingredients** from your pantry. This cannot be undone.")
    col_confirm, col_cancel = st.columns(2)
    with col_confirm:
        if st.button("Yes, clear everything", type="primary", width="stretch"):
            clear_all_ingredients()
            st.rerun(scope="app")
    with col_cancel:
        if st.button("Cancel", width="stretch"):
            st.rerun(scope="app")


# ---------------------------------------------------------------------------
# Current ingredients list
# ---------------------------------------------------------------------------
head_col, btn_col = st.columns([5, 1])
with head_col:
    st.subheader("Current Ingredients")
with btn_col:
    st.write("")
    if st.button("🗑️ Clear All", width="stretch", type="secondary"):
        confirm_clear_pantry()

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


def format_expiry(expiry_str):
    if not expiry_str:
        return '<span style="color:#9ca3af;">—</span>'
    try:
        expiry = date.fromisoformat(expiry_str)
        days_left = (expiry - date.today()).days
        if days_left < 0:
            return f'<span style="color:#ef4444;font-weight:600;">Expired {abs(days_left)}d ago</span>'
        elif days_left == 0:
            return '<span style="color:#ef4444;font-weight:600;">Today</span>'
        elif days_left == 1:
            return '<span style="color:#f97316;font-weight:600;">Tomorrow</span>'
        elif days_left <= 3:
            return f'<span style="color:#f59e0b;font-weight:600;">In {days_left}d</span>'
        else:
            return expiry.strftime("%b %d")
    except Exception:
        return "—"


if not ingredients:
    st.info("Your pantry is empty. Add some ingredients above.")
else:
    hcol1, hcol2, hcol3, hcol4, hcol5, hcol6, hcol7 = st.columns([2.0, 1.5, 1.5, 1.5, 1.5, 1.0, 1.0])
    with hcol1: st.markdown("**Ingredient**")
    with hcol2: st.markdown("**Amount**")
    with hcol3: st.markdown("**Location**")
    with hcol4: st.markdown("**Added Date**")
    with hcol5: st.markdown("**Expiry**")
    st.divider()

    for ingredient in ingredients:
        col1, col2, col3, col4, col5, col6, col7 = st.columns([2.0, 1.5, 1.5, 1.5, 1.5, 1.0, 1.0])
        loc = ingredient.get("location") or "Fridge"
        with col1:
            st.write(f"**{ingredient['name']}**")
        with col2:
            st.write(f"{ingredient['amount']} {ingredient['unit']}")
        with col3:
            icon = LOCATION_ICONS.get(loc, "📦")
            st.write(f"{icon} {loc}")
        with col4:
            st.caption(format_dates(ingredient["added_date"], ingredient.get("updated_date")))
        with col5:
            st.markdown(format_expiry(ingredient.get("expiry_date")), unsafe_allow_html=True)
        with col6:
            if st.button("Edit", key=f"edit_btn_{ingredient['id']}"):
                st.session_state["editing_id"] = ingredient["id"]
        with col7:
            if st.button("Remove", key=f"del_{ingredient['id']}"):
                delete_ingredient(ingredient["id"])
                if st.session_state.get("editing_id") == ingredient["id"]:
                    del st.session_state["editing_id"]
                st.rerun()

        if st.session_state.get("editing_id") == ingredient["id"]:
            with st.form(f"edit_form_{ingredient['id']}"):
                edit_col1, edit_col2, edit_col3 = st.columns(3)
                with edit_col1:
                    new_amount = st.number_input(
                        f"Amount",
                        min_value=0.1,
                        value=float(ingredient["amount"]),
                        step=0.5,
                    )
                with edit_col2:
                    current_loc = ingredient.get("location") or "Fridge"
                    loc_idx = LOCATIONS.index(current_loc) if current_loc in LOCATIONS else 0
                    new_location = st.selectbox("Location", LOCATIONS, index=loc_idx)
                with edit_col3:
                    current_expiry = ingredient.get("expiry_date")
                    expiry_value = date.fromisoformat(current_expiry) if current_expiry else None
                    new_expiry = st.date_input("Expiry date (optional)", value=expiry_value)
                col_save, col_cancel = st.columns(2)
                with col_save:
                    if st.form_submit_button("Save", width="stretch"):
                        expiry_str = new_expiry.isoformat() if new_expiry else None
                        update_ingredient(ingredient["id"], new_amount, new_location, expiry_str)
                        del st.session_state["editing_id"]
                        st.rerun()
                with col_cancel:
                    if st.form_submit_button("Cancel", width="stretch"):
                        del st.session_state["editing_id"]
                        st.rerun()
