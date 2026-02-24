import os
import io
from google import genai
from google.genai import types
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = "gemini-2.5-flash"


def _get_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found. Check your .env file or Streamlit secrets.")
    return genai.Client(api_key=api_key)


RECIPE_EXTRACTION_PROMPT = """
    Extract recipe information from the provided file(s). There may be one or two pages —
    for example, a recipe card with ingredients on the front and cooking steps on the back.
    Combine all information across pages into a single recipe.

    Return ONLY valid JSON with no extra text or markdown:

    {
        "name": "recipe name",
        "cooking_time": "total cooking time as a string (e.g. '30 minutes')",
        "ingredients": [
            {"name": "ingredient name", "amount": numeric_value, "unit": "unit of measurement"}
        ],
        "instructions": "step by step cooking instructions as a single string"
    }

    For units, use natural and specific terms. Examples:
    - Produce (tomatoes, onions, lemons): whole, half, quarter, slice
    - Garlic: clove
    - Leafy greens, herbs: head, bunch, stalk, sprig, leaf
    - Meat, cheese, butter: grams, oz, lbs
    - Liquids, oils: ml, cups, tablespoons, teaspoons
    - Packaged goods: can, jar, bag, box
    - If truly countable with no better option: piece

    If you cannot determine an amount, use null.
    If you cannot determine a unit, use null.
"""


def _parse_gemini_json(text):
    import json
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def extract_recipe_from_images(image_bytes_list):
    """Extract recipe from one or more images (e.g. front and back of a recipe card)."""
    client = _get_client()
    images = [Image.open(io.BytesIO(b)) for b in image_bytes_list]
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[RECIPE_EXTRACTION_PROMPT] + images,
    )
    return _parse_gemini_json(response.text)


def extract_recipe_from_pdf(pdf_bytes):
    """Extract recipe from a PDF (handles multiple pages automatically)."""
    from google.genai import types
    client = _get_client()
    pdf_part = types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf")
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[RECIPE_EXTRACTION_PROMPT, pdf_part],
    )
    return _parse_gemini_json(response.text)


def get_storage_tips(ingredient_names):
    """Return a one-sentence storage tip for each ingredient name."""
    client = _get_client()
    names_list = "\n".join([f"- {name}" for name in ingredient_names])
    prompt = f"""Give a brief storage tip for each ingredient below.
Each tip should say where to store it (fridge, pantry, freezer, etc.) and the rough shelf life.
Keep each tip to one sentence, 15 words or fewer.

Ingredients:
{names_list}

Return ONLY valid JSON with no extra text or markdown, using the exact ingredient names as keys:
{{
    "Ingredient Name": "storage tip",
    ...
}}"""
    response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
    return _parse_gemini_json(response.text)


def suggest_recipes(fridge_ingredients, stored_recipes):
    """Suggest recipes based on current fridge contents."""
    client = _get_client()

    fridge_list = "\n".join(
        [f"- {i['name']}: {i['amount']} {i['unit']}" for i in fridge_ingredients]
    )
    saved_list = "\n".join([f"- {r['name']}" for r in stored_recipes])

    prompt = f"""
    I have these ingredients in my fridge:
    {fridge_list}

    I have these saved recipes:
    {saved_list if saved_list else "No saved recipes yet."}

    Please provide:
    1. Which of my saved recipes I can make with what I have, and note any missing ingredients.
    2. 2-3 additional simple recipe ideas based on my ingredients (even if not in my saved list).

    Keep the response clear and practical with headers for each section.
    """

    response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
    return response.text


def generate_meal_plan(recipes, days=7):
    """Generate a meal plan using saved recipes."""
    client = _get_client()

    if not recipes:
        return "No saved recipes found. Please add some recipes first."

    recipe_list = "\n".join(
        [f"- {r['name']} (cooking time: {r['cooking_time']})" for r in recipes]
    )

    prompt = f"""
    I have these recipes available:
    {recipe_list}

    Create a {days}-day meal plan. Include breakfast, lunch, and dinner for each day.
    Use my saved recipes where they fit and suggest simple ideas for any gaps.
    Format it as a clear day-by-day schedule.
    """

    response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
    return response.text


def generate_home_insight(fridge_ingredients, recipes, cookable_recipes, forgotten_ingredients):
    """Generate actionable insights for the home dashboard."""
    client = _get_client()

    fridge_list = "\n".join(
        [f"- {i['name']}: {i['amount']} {i['unit']}" for i in fridge_ingredients]
    ) if fridge_ingredients else "Fridge is empty."

    cookable_names = ", ".join([r["name"] for r in cookable_recipes]) if cookable_recipes else "none"
    forgotten_names = ", ".join([i["name"] for i in forgotten_ingredients]) if forgotten_ingredients else "none"

    prompt = f"""
    I have a fridge with these ingredients:
    {fridge_list}

    Recipes I can make right now with these ingredients: {cookable_names}
    Ingredients in my fridge not used in any saved recipe: {forgotten_names}

    Give me 2-3 short, specific, actionable insights such as:
    - What I should cook soon to make good use of my ingredients
    - Any ingredients I should prioritize before they go to waste
    - A quick suggestion based on my current inventory

    Be direct and practical. Format as short bullet points. Keep it under 100 words total.
    """

    response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
    return response.text


def suggest_calendar_meals(recipes, unplanned_dates, current_week_plan):
    """Suggest recipes from the saved list for unplanned days in the calendar."""
    client = _get_client()

    recipe_list = "\n".join(
        [f"- {r['name']} (cooking time: {r['cooking_time']})" for r in recipes]
    )

    special = {"— Unplanned —", "🍽️ Eating Out", "🏖️ Vacation / Skip"}
    already_planned = {d: v for d, v in current_week_plan.items() if v not in special}
    planned_str = (
        "\n".join([f"- {d}: {v}" for d, v in sorted(already_planned.items())])
        if already_planned
        else "None yet."
    )
    unplanned_str = "\n".join([f"- {d}" for d in sorted(unplanned_dates)])

    prompt = f"""
    I'm planning meals for the week. My saved recipes are:
    {recipe_list}

    Already planned:
    {planned_str}

    Please suggest one recipe for each of these unplanned days:
    {unplanned_str}

    Choose from my saved recipes only. Vary the choices — avoid repeating the same recipe on consecutive days if possible.

    Return ONLY valid JSON with no extra text or markdown, in this exact format:
    {{
        "YYYY-MM-DD": "Recipe Name",
        "YYYY-MM-DD": "Recipe Name"
    }}

    Only include dates from the unplanned list above. Use exact recipe names as listed.
    """

    response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
    return _parse_gemini_json(response.text)


def generate_weekly_shopping_list(meal_plan, planned_recipes, fridge_ingredients):
    """Generate a consolidated shopping list for a week's planned meals."""
    client = _get_client()

    fridge_list = (
        "\n".join([f"- {i['name']}: {i['amount']} {i['unit']}" for i in fridge_ingredients])
        if fridge_ingredients
        else "Fridge is empty."
    )

    meals_str = "\n".join([f"- {d}: {v}" for d, v in sorted(meal_plan.items())])

    # Aggregate ingredients across all planned meals
    ingredient_lines = []
    for recipe in planned_recipes:
        times = list(meal_plan.values()).count(recipe["name"])
        for ing in recipe["ingredients"]:
            total = ing["amount"] * times
            suffix = f" ×{times}" if times > 1 else ""
            ingredient_lines.append(
                f"- {ing['name']}: {total} {ing['unit']} (for {recipe['name']}{suffix})"
            )
    ingredients_str = "\n".join(ingredient_lines) if ingredient_lines else "No ingredients."

    prompt = f"""
    My meal plan for the week:
    {meals_str}

    Total ingredients needed across all planned meals:
    {ingredients_str}

    What I currently have in my fridge:
    {fridge_list}

    Create a consolidated weekly shopping list. Group items by category (Produce, Proteins, Dairy, Pantry, etc.).
    Account for what I already have — only list what I still need to buy.
    If I need more of something than I have, note how much extra to buy.

    Format clearly with category headers and bullet points.
    """

    response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
    return response.text


def reschedule_around_grocery_date(meal_plan, recipes, pantry_ingredients, grocery_date_str):
    """
    Rearrange a meal plan so that meals before grocery_date only use current pantry.
    Meals requiring shopping are pushed to grocery_date or after.

    meal_plan: {date_str: {meal_type: meal_name}}
    recipes:   full recipe list from get_recipes()
    pantry_ingredients: list of ingredient dicts from get_ingredients()
    grocery_date_str: ISO date string of when the user can next shop

    Returns parsed JSON: {"feasible": bool, "note": str, "plan": {date_str: {meal_type: meal_name}}}
    """
    client = _get_client()

    plan_lines = []
    for date_str, meals in sorted(meal_plan.items()):
        for meal_type, meal_name in meals.items():
            plan_lines.append(f"- {date_str} {meal_type}: {meal_name}")
    plan_str = "\n".join(plan_lines) if plan_lines else "No meals planned."

    pantry_str = "\n".join(
        [f"- {i['name']}: {i['amount']} {i['unit']}" for i in pantry_ingredients]
    ) if pantry_ingredients else "Pantry is empty."

    recipe_lines = []
    for r in recipes:
        ings = ", ".join([f"{i['name']} ({i['amount']} {i['unit']})" for i in r["ingredients"]])
        recipe_lines.append(f"- {r['name']}: needs {ings}")
    recipes_str = "\n".join(recipe_lines) if recipe_lines else "No recipes saved."

    prompt = f"""
I have a meal plan for the next 7 days but I cannot go grocery shopping until {grocery_date_str}.

Current meal plan:
{plan_str}

My current pantry:
{pantry_str}

My saved recipes and their ingredients:
{recipes_str}

Please rearrange my meal plan so that:
1. All meals scheduled BEFORE {grocery_date_str} only use ingredients I currently have in my pantry
2. Meals that require ingredients not in my pantry are moved to {grocery_date_str} or later
3. The week still makes sense — avoid the same recipe on consecutive days where possible
4. Only use recipe names exactly as listed above, or "— Unplanned —" if a slot can't be filled

If you cannot fill every slot before {grocery_date_str} with pantry-only meals, leave those slots as "— Unplanned —" and set "feasible" to false with a note explaining what's missing.

Return ONLY valid JSON with no extra text or markdown:
{{
    "feasible": true,
    "note": "Brief message to the user about the rescheduled plan, or what's missing if not feasible",
    "plan": {{
        "YYYY-MM-DD": {{
            "Breakfast": "Recipe Name or — Unplanned —",
            "Lunch": "Recipe Name or — Unplanned —",
            "Dinner": "Recipe Name or — Unplanned —"
        }}
    }}
}}

Include all 7 days. Use the exact date strings from the current plan.
"""

    response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
    return _parse_gemini_json(response.text)


def generate_shopping_list(recipe, fridge_ingredients):
    """Compare a recipe's ingredients against the fridge and list what to buy."""
    client = _get_client()

    fridge_list = "\n".join(
        [f"- {i['name']}: {i['amount']} {i['unit']}" for i in fridge_ingredients]
    )
    recipe_ingredients = "\n".join(
        [f"- {i['name']}: {i['amount']} {i['unit']}" for i in recipe["ingredients"]]
    )

    prompt = f"""
    I want to make: {recipe['name']}

    This recipe requires:
    {recipe_ingredients}

    I currently have in my fridge:
    {fridge_list}

    Compare what the recipe needs against what I have. List:
    1. Ingredients I already have (and whether I have enough)
    2. Ingredients I need to buy (with the amounts needed)

    Be specific and practical.
    """

    response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
    return response.text
