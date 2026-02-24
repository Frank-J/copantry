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
