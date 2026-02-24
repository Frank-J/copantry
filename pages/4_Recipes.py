import streamlit as st
from database import get_recipes, add_recipe, update_recipe, delete_recipe, log_recipe_cooked
from gemini_client import extract_recipe_from_images, extract_recipe_from_pdf
from constants import UNITS

st.set_page_config(page_title="Recipes", page_icon="📖", layout="wide")

st.title("📖 Recipes")

st.divider()

# Add recipe section
tab1, tab2 = st.tabs(["📷 Add via Photo or PDF", "✏️ Add Manually"])

with tab1:
    st.subheader("Upload a Recipe Photo or PDF")
    st.markdown("Upload a photo or PDF and AI will extract the name, ingredients, cooking time, and instructions automatically.")

    st.info(
        "**One recipe per upload.** Uploading multiple recipes at once will mix their ingredients together. "
        "For recipe cards with a front and back (e.g. HelloFresh), upload both sides together — the AI will combine them."
    )

    uploaded_files = st.file_uploader(
        "Choose a recipe photo or PDF (up to 2 images for front and back)",
        type=["jpg", "jpeg", "png", "webp", "pdf"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        is_pdf = any(f.name.lower().endswith(".pdf") for f in uploaded_files)

        if is_pdf and len(uploaded_files) > 1:
            st.error("Please upload only one PDF at a time.")
        elif not is_pdf and len(uploaded_files) > 2:
            st.error("Please upload a maximum of 2 images (front and back of a recipe card).")
        else:
            for f in uploaded_files:
                if not f.name.lower().endswith(".pdf"):
                    st.image(f, caption=f.name, use_container_width=True)
                else:
                    st.markdown(f"📄 **{f.name}** ready to extract.")

            if st.button("Extract Recipe with AI", use_container_width=True):
                with st.spinner("Analysing your recipe..."):
                    try:
                        if is_pdf:
                            result = extract_recipe_from_pdf(uploaded_files[0].getvalue())
                        else:
                            result = extract_recipe_from_images([f.getvalue() for f in uploaded_files])
                        st.session_state["extracted_recipe"] = result
                    except Exception as e:
                        st.error(f"Could not extract recipe: {e}")

    if "extracted_recipe" in st.session_state:
        recipe = st.session_state["extracted_recipe"]
        st.success("Recipe extracted! Review and complete any missing fields before saving.")

        with st.form("save_extracted_recipe"):
            name = st.text_input("Recipe Name", value=recipe.get("name", ""))
            cooking_time = st.text_input("Cooking Time", value=recipe.get("cooking_time", ""))
            instructions = st.text_area("Instructions", value=recipe.get("instructions", ""), height=150)

            st.markdown("**Ingredients** — fill in any fields marked with ⚠️")
            st.caption("Name · Amount · Unit")

            extracted_ingredients = recipe.get("ingredients", [])
            edited_ingredients = []

            for i, ing in enumerate(extracted_ingredients):
                col1, col2, col3 = st.columns([3, 2, 2])

                missing_amount = ing.get("amount") is None
                missing_unit = ing.get("unit") is None or ing.get("unit") not in UNITS

                with col1:
                    ing_name = st.text_input(
                        "Name",
                        value=ing.get("name", ""),
                        key=f"ing_name_{i}",
                        label_visibility="collapsed",
                    )
                with col2:
                    ing_amount = st.number_input(
                        "⚠️ Amount needed" if missing_amount else "Amount",
                        min_value=0.0,
                        value=float(ing.get("amount") or 0.0),
                        step=0.5,
                        key=f"ing_amount_{i}",
                        label_visibility="visible" if missing_amount else "collapsed",
                    )
                with col3:
                    ing_unit = st.selectbox(
                        "⚠️ Unit needed" if missing_unit else "Unit",
                        UNITS,
                        index=0 if missing_unit else UNITS.index(ing.get("unit")),
                        key=f"ing_unit_{i}",
                        label_visibility="visible" if missing_unit else "collapsed",
                    )

                edited_ingredients.append({
                    "name": ing_name,
                    "amount": ing_amount,
                    "unit": ing_unit,
                })

            if st.form_submit_button("Save Recipe", use_container_width=True):
                errors = []
                if not name.strip():
                    errors.append("Recipe name is required.")
                for j, ing in enumerate(edited_ingredients):
                    if not ing["name"].strip():
                        errors.append(f"Ingredient {j + 1} is missing a name.")
                    if ing["amount"] <= 0:
                        errors.append(f"'{ing['name']}' needs an amount greater than 0.")

                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    add_recipe(name, cooking_time, edited_ingredients, instructions)
                    del st.session_state["extracted_recipe"]
                    st.success(f"'{name}' saved!")
                    st.rerun()

with tab2:
    st.subheader("Add Recipe Manually")
    with st.form("manual_recipe_form", clear_on_submit=True):
        name = st.text_input("Recipe Name")
        cooking_time = st.text_input("Cooking Time", placeholder="e.g. 30 minutes")
        instructions = st.text_area("Instructions", placeholder="Step by step instructions...", height=150)

        st.markdown("**Ingredients** — one per line in the format: `Name, Amount, Unit`")
        st.caption("Unit examples: whole, half, quarter, slice, clove, head, bunch, grams, kg, oz, lbs, ml, cups, tablespoons, teaspoons, can, bag")
        ingredients_text = st.text_area(
            "Ingredients",
            placeholder="Eggs, 3, whole\nMilk, 1, cups\nButter, 50, grams\nTomatoes, 2, whole",
            height=120,
        )

        if st.form_submit_button("Save Recipe", use_container_width=True):
            if name.strip():
                ingredients = []
                for line in ingredients_text.strip().split("\n"):
                    if line.strip():
                        parts = [p.strip() for p in line.split(",")]
                        if len(parts) >= 3:
                            try:
                                ingredients.append({
                                    "name": parts[0],
                                    "amount": float(parts[1]),
                                    "unit": parts[2],
                                })
                            except ValueError:
                                pass
                add_recipe(name.strip(), cooking_time.strip(), ingredients, instructions.strip())
                st.success(f"'{name}' saved!")
                st.rerun()
            else:
                st.error("Please enter a recipe name.")

st.divider()

# Saved recipes list
st.subheader("Saved Recipes")
recipes = get_recipes()

if not recipes:
    st.info("No recipes saved yet. Add one above.")
else:
    for recipe in recipes:
        with st.expander(f"**{recipe['name']}** — {recipe['cooking_time']}"):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown("**Ingredients:**")
                for ing in recipe["ingredients"]:
                    st.write(f"- {ing['name']}: {ing['amount']} {ing['unit']}")
                if recipe["instructions"]:
                    st.markdown("**Instructions:**")
                    st.write(recipe["instructions"])
            with col2:
                if st.button("✅ Cooked", key=f"cooked_{recipe['id']}"):
                    log_recipe_cooked(recipe["id"])
                    st.success("Logged!")
                if st.button("✏️ Edit", key=f"edit_recipe_{recipe['id']}"):
                    st.session_state["editing_recipe_id"] = recipe["id"]
                    st.rerun()
                if st.button("Delete", key=f"del_recipe_{recipe['id']}"):
                    delete_recipe(recipe["id"])
                    if st.session_state.get("editing_recipe_id") == recipe["id"]:
                        del st.session_state["editing_recipe_id"]
                    st.rerun()

    # Inline edit form — appears below the list when a recipe is being edited
    editing_id = st.session_state.get("editing_recipe_id")
    if editing_id:
        recipe_to_edit = next((r for r in recipes if r["id"] == editing_id), None)
        if recipe_to_edit:
            st.divider()
            st.subheader(f"✏️ Editing: {recipe_to_edit['name']}")

            with st.form("edit_recipe_form"):
                edit_name = st.text_input("Recipe Name", value=recipe_to_edit["name"])
                edit_cooking_time = st.text_input("Cooking Time", value=recipe_to_edit["cooking_time"] or "")
                edit_instructions = st.text_area("Instructions", value=recipe_to_edit["instructions"] or "", height=150)

                st.markdown("**Existing Ingredients** — edit below (clear a name to remove it)")
                st.caption("Name · Amount · Unit")

                edited_ingredients = []
                for i, ing in enumerate(recipe_to_edit["ingredients"]):
                    col1, col2, col3 = st.columns([3, 2, 2])
                    with col1:
                        ing_name = st.text_input("Name", value=ing["name"], key=f"edit_ing_name_{i}", label_visibility="collapsed")
                    with col2:
                        ing_amount = st.number_input("Amount", min_value=0.0, value=float(ing["amount"]), step=0.5, key=f"edit_ing_amount_{i}", label_visibility="collapsed")
                    with col3:
                        unit_index = UNITS.index(ing["unit"]) if ing["unit"] in UNITS else 0
                        ing_unit = st.selectbox("Unit", UNITS, index=unit_index, key=f"edit_ing_unit_{i}", label_visibility="collapsed")
                    if ing_name.strip():
                        edited_ingredients.append({"name": ing_name.strip(), "amount": ing_amount, "unit": ing_unit})

                st.markdown("**Add More Ingredients** — one per line: `Name, Amount, Unit`")
                new_ingredients_text = st.text_area("New ingredients", placeholder="Lemon, 1, whole\nParsley, 1, bunch", height=80, label_visibility="collapsed")

                col_save, col_cancel = st.columns(2)
                with col_save:
                    save = st.form_submit_button("Save Changes", use_container_width=True, type="primary")
                with col_cancel:
                    cancel = st.form_submit_button("Cancel", use_container_width=True)

                if save:
                    for line in new_ingredients_text.strip().split("\n"):
                        if line.strip():
                            parts = [p.strip() for p in line.split(",")]
                            if len(parts) >= 3:
                                try:
                                    edited_ingredients.append({"name": parts[0], "amount": float(parts[1]), "unit": parts[2]})
                                except ValueError:
                                    pass
                    if not edit_name.strip():
                        st.error("Recipe name is required.")
                    elif not edited_ingredients:
                        st.error("At least one ingredient is required.")
                    else:
                        update_recipe(editing_id, edit_name.strip(), edit_cooking_time.strip(), edited_ingredients, edit_instructions.strip())
                        del st.session_state["editing_recipe_id"]
                        st.success(f"'{edit_name}' updated!")
                        st.rerun()

                if cancel:
                    del st.session_state["editing_recipe_id"]
                    st.rerun()
