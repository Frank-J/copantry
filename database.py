import sqlite3
import json
from datetime import datetime, timedelta, date

DB_PATH = "recipes.db"

# ---------------------------------------------------------------------------
# Unit conversion helpers
# ---------------------------------------------------------------------------

UNIT_TO_GRAMS = {"grams": 1, "kg": 1000, "oz": 28.3495, "lbs": 453.592}
UNIT_TO_ML = {"ml": 1, "liters": 1000, "cups": 240, "tablespoons": 14.787, "teaspoons": 4.929}


def _to_base(amount, unit):
    """Convert amount to a base unit (grams or ml). Returns (base_amount, base_unit).
    Countable/packaged units are returned unchanged."""
    if unit in UNIT_TO_GRAMS:
        return amount * UNIT_TO_GRAMS[unit], "grams"
    if unit in UNIT_TO_ML:
        return amount * UNIT_TO_ML[unit], "ml"
    return amount, unit


def _from_base(base_amount, target_unit):
    """Convert a base-unit amount back to the target unit."""
    if target_unit in UNIT_TO_GRAMS:
        return base_amount / UNIT_TO_GRAMS[target_unit]
    if target_unit in UNIT_TO_ML:
        return base_amount / UNIT_TO_ML[target_unit]
    return base_amount


def _has_enough(fridge_amount, fridge_unit, need_amount, need_unit):
    """Return True if fridge has enough, False if not, None if units are incomparable."""
    f_base, f_base_unit = _to_base(fridge_amount, fridge_unit)
    n_base, n_base_unit = _to_base(need_amount, need_unit)
    if f_base_unit != n_base_unit:
        return None  # e.g. grams vs cups — can't compare
    return f_base >= n_base


def get_connection():
    return sqlite3.connect(DB_PATH)


def initialize_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            unit TEXT NOT NULL,
            added_date TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            cooking_time TEXT,
            ingredients TEXT NOT NULL,
            instructions TEXT,
            created_at TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS recipe_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER NOT NULL,
            cooked_at TEXT NOT NULL,
            FOREIGN KEY (recipe_id) REFERENCES recipes(id)
        )
    """)

    # Seed sample data only if tables are empty
    now = datetime.now()
    ago = lambda days: (now - timedelta(days=days)).isoformat()

    c.execute("SELECT COUNT(*) FROM ingredients")
    if c.fetchone()[0] == 0:
        sample_ingredients = [
            # Used in recipes
            ("Eggs", 6, "whole", ago(1)),
            ("Milk", 2, "cups", ago(1)),
            ("Butter", 200, "grams", ago(3)),
            ("Pasta", 500, "grams", ago(3)),
            ("Tomatoes", 4, "whole", ago(2)),
            ("Garlic", 5, "cloves", ago(5)),
            ("Olive Oil", 1, "cups", ago(7)),
            ("Chicken Breast", 500, "grams", ago(2)),
            ("Onion", 2, "whole", ago(4)),
            # Forgotten — in fridge but not in any recipe
            ("Cornstarch", 1, "tablespoons", ago(14)),
            ("Lettuce", 1, "head", ago(5)),
        ]
        c.executemany(
            "INSERT INTO ingredients (name, amount, unit, added_date) VALUES (?, ?, ?, ?)",
            sample_ingredients,
        )

    c.execute("SELECT COUNT(*) FROM recipes")
    if c.fetchone()[0] == 0:
        sample_recipes = [
            (
                "Scrambled Eggs",
                "10 minutes",
                json.dumps([
                    {"name": "Eggs", "amount": 3, "unit": "whole"},
                    {"name": "Milk", "amount": 0.25, "unit": "cups"},
                    {"name": "Butter", "amount": 20, "unit": "grams"},
                ]),
                "1. Whisk eggs and milk together. 2. Melt butter in a pan over low heat. 3. Add egg mixture and stir gently until just set.",
                ago(14),
            ),
            (
                "Spaghetti Aglio e Olio",
                "20 minutes",
                json.dumps([
                    {"name": "Pasta", "amount": 200, "unit": "grams"},
                    {"name": "Garlic", "amount": 4, "unit": "cloves"},
                    {"name": "Olive Oil", "amount": 0.25, "unit": "cups"},
                ]),
                "1. Cook pasta in salted boiling water. 2. Slice garlic thinly and sauté in olive oil until golden. 3. Toss drained pasta with garlic oil. Season with salt and pepper.",
                ago(12),
            ),
            (
                "Garlic Butter Chicken",
                "35 minutes",
                json.dumps([
                    {"name": "Chicken Breast", "amount": 500, "unit": "grams"},
                    {"name": "Butter", "amount": 30, "unit": "grams"},
                    {"name": "Garlic", "amount": 3, "unit": "cloves"},
                    {"name": "Olive Oil", "amount": 2, "unit": "tablespoons"},
                ]),
                "1. Season chicken with salt and pepper. 2. Heat olive oil in a pan over medium-high heat. 3. Cook chicken 6-7 minutes per side. 4. Add butter and garlic, baste chicken for 2 minutes.",
                ago(10),
            ),
            (
                "Tomato Pasta",
                "25 minutes",
                json.dumps([
                    {"name": "Pasta", "amount": 200, "unit": "grams"},
                    {"name": "Tomatoes", "amount": 3, "unit": "whole"},
                    {"name": "Garlic", "amount": 2, "unit": "cloves"},
                    {"name": "Olive Oil", "amount": 3, "unit": "tablespoons"},
                    {"name": "Onion", "amount": 1, "unit": "whole"},
                ]),
                "1. Dice tomatoes and onion. 2. Sauté garlic and onion in olive oil. 3. Add tomatoes and simmer 10 minutes. 4. Toss with cooked pasta.",
                ago(7),
            ),
            (
                "Lemon Herb Salmon",
                "25 minutes",
                json.dumps([
                    {"name": "Salmon", "amount": 500, "unit": "grams"},
                    {"name": "Lemon", "amount": 2, "unit": "whole"},
                    {"name": "Butter", "amount": 30, "unit": "grams"},
                    {"name": "Garlic", "amount": 2, "unit": "cloves"},
                ]),
                "1. Season salmon with salt and pepper. 2. Melt butter in a pan. 3. Cook salmon 4 minutes each side. 4. Add garlic and squeeze lemon over the top.",
                ago(5),
            ),
        ]
        c.executemany(
            "INSERT INTO recipes (name, cooking_time, ingredients, instructions, created_at) VALUES (?, ?, ?, ?, ?)",
            sample_recipes,
        )

        # Seed cooking history using the inserted recipe IDs
        c.execute("SELECT id, name FROM recipes")
        recipe_map = {name: rid for rid, name in c.fetchall()}

        usage_entries = [
            # Scrambled Eggs — most cooked (4 times)
            (recipe_map["Scrambled Eggs"], ago(1)),
            (recipe_map["Scrambled Eggs"], ago(4)),
            (recipe_map["Scrambled Eggs"], ago(8)),
            (recipe_map["Scrambled Eggs"], ago(13)),
            # Spaghetti Aglio e Olio — 3 times
            (recipe_map["Spaghetti Aglio e Olio"], ago(2)),
            (recipe_map["Spaghetti Aglio e Olio"], ago(6)),
            (recipe_map["Spaghetti Aglio e Olio"], ago(11)),
            # Garlic Butter Chicken — 2 times
            (recipe_map["Garlic Butter Chicken"], ago(3)),
            (recipe_map["Garlic Butter Chicken"], ago(9)),
            # Tomato Pasta — 1 time
            (recipe_map["Tomato Pasta"], ago(7)),
        ]
        c.executemany(
            "INSERT INTO recipe_usage (recipe_id, cooked_at) VALUES (?, ?)",
            usage_entries,
        )

    # Migrate: add updated_date column if it doesn't exist yet
    try:
        c.execute("ALTER TABLE ingredients ADD COLUMN updated_date TEXT")
        c.execute("UPDATE ingredients SET updated_date = added_date WHERE updated_date IS NULL")
    except sqlite3.OperationalError:
        pass  # column already exists

    conn.commit()
    conn.close()


# Ingredient operations

def add_ingredient(name, amount, unit):
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute(
        "INSERT INTO ingredients (name, amount, unit, added_date, updated_date) VALUES (?, ?, ?, ?, ?)",
        (name, amount, unit, now, now),
    )
    conn.commit()
    conn.close()


def get_ingredients():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, amount, unit, added_date, updated_date FROM ingredients ORDER BY name")
    rows = c.fetchall()
    conn.close()
    return [
        {"id": r[0], "name": r[1], "amount": r[2], "unit": r[3], "added_date": r[4], "updated_date": r[5]}
        for r in rows
    ]


def delete_ingredient(ingredient_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM ingredients WHERE id = ?", (ingredient_id,))
    conn.commit()
    conn.close()


def update_ingredient_amount(ingredient_id, amount):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE ingredients SET amount = ?, updated_date = ? WHERE id = ?",
        (amount, datetime.now().isoformat(), ingredient_id),
    )
    conn.commit()
    conn.close()


# Recipe operations

def add_recipe(name, cooking_time, ingredients, instructions):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO recipes (name, cooking_time, ingredients, instructions, created_at) VALUES (?, ?, ?, ?, ?)",
        (name, cooking_time, json.dumps(ingredients), instructions, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_recipes():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, cooking_time, ingredients, instructions FROM recipes ORDER BY name")
    rows = c.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "name": r[1],
            "cooking_time": r[2],
            "ingredients": json.loads(r[3]),
            "instructions": r[4],
        }
        for r in rows
    ]


def update_recipe(recipe_id, name, cooking_time, ingredients, instructions):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE recipes SET name = ?, cooking_time = ?, ingredients = ?, instructions = ? WHERE id = ?",
        (name, cooking_time, json.dumps(ingredients), instructions, recipe_id),
    )
    conn.commit()
    conn.close()


def delete_recipe(recipe_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
    c.execute("DELETE FROM recipe_usage WHERE recipe_id = ?", (recipe_id,))
    conn.commit()
    conn.close()


# Usage tracking

def log_recipe_cooked(recipe_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO recipe_usage (recipe_id, cooked_at) VALUES (?, ?)",
        (recipe_id, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_most_cooked_recipes(limit=5):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT r.name, COUNT(ru.id) as cook_count
        FROM recipes r
        JOIN recipe_usage ru ON r.id = ru.recipe_id
        GROUP BY r.id, r.name
        ORDER BY cook_count DESC
        LIMIT ?
    """, (limit,))
    rows = c.fetchall()
    conn.close()
    return [{"name": r[0], "count": r[1]} for r in rows]


def get_most_used_ingredients(limit=5):
    """Derive most used ingredients from cooked recipe history."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT r.ingredients, COUNT(ru.id) as cook_count
        FROM recipes r
        JOIN recipe_usage ru ON r.id = ru.recipe_id
        GROUP BY r.id
    """)
    rows = c.fetchall()
    conn.close()

    ingredient_counts = {}
    for row in rows:
        ingredients = json.loads(row[0])
        cook_count = row[1]
        for ing in ingredients:
            name = ing["name"].lower()
            ingredient_counts[name] = ingredient_counts.get(name, 0) + cook_count

    sorted_ingredients = sorted(ingredient_counts.items(), key=lambda x: x[1], reverse=True)
    return [{"name": name.title(), "count": count} for name, count in sorted_ingredients[:limit]]


def get_cookable_recipes():
    """Return recipes where all ingredients are present in sufficient quantity."""
    fridge = get_ingredients()
    recipes = get_recipes()
    fridge_map = {i["name"].lower(): i for i in fridge}

    cookable = []
    for recipe in recipes:
        can_cook = True
        for ing in recipe["ingredients"]:
            fridge_item = fridge_map.get(ing["name"].lower())
            if not fridge_item:
                can_cook = False
                break
            result = _has_enough(fridge_item["amount"], fridge_item["unit"], ing["amount"], ing["unit"])
            if result is False:  # None means incomparable units — don't block
                can_cook = False
                break
        if can_cook:
            cookable.append(recipe)
    return cookable


def deduct_recipe_ingredients(recipe_id):
    """Subtract recipe ingredient amounts from the fridge after cooking."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT ingredients FROM recipes WHERE id = ?", (recipe_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return
    ingredients = json.loads(row[0])
    for ing in ingredients:
        c.execute(
            "SELECT id, amount, unit FROM ingredients WHERE LOWER(name) = LOWER(?)",
            (ing["name"],),
        )
        fridge_row = c.fetchone()
        if not fridge_row:
            continue
        fridge_id, fridge_amount, fridge_unit = fridge_row
        f_base, f_base_unit = _to_base(fridge_amount, fridge_unit)
        n_base, n_base_unit = _to_base(ing["amount"], ing["unit"])
        if f_base_unit != n_base_unit:
            continue  # incomparable units — skip
        remaining = _from_base(max(0, f_base - n_base), fridge_unit)
        if remaining <= 0:
            c.execute("DELETE FROM ingredients WHERE id = ?", (fridge_id,))
        else:
            c.execute(
                "UPDATE ingredients SET amount = ?, updated_date = ? WHERE id = ?",
                (round(remaining, 3), datetime.now().isoformat(), fridge_id),
            )
    conn.commit()
    conn.close()


def get_shopping_plan(meal_plan, recipes):
    """
    Project ingredient depletion across a meal plan and return a shopping plan.

    meal_plan: {date_str: recipe_name} — only home meals (no special values)
    recipes:   full recipe list from get_recipes()

    Returns:
    {
        "fully_covered": bool,
        "shop_by": date_str | None,   # day before first shortage
        "items": [
            {
                "name": str,
                "need_amount": float, "need_unit": str,   # per recipe serving
                "have_amount": float, "have_unit": str,   # what was left before shortage
                "runs_out_on": date_str,
                "recipe": str,
            }
        ]
    }
    """
    fridge = get_ingredients()
    recipe_map = {r["name"]: r for r in recipes}

    # Build running inventory keyed by lowercase name, storing base amounts
    inventory = {}
    for item in fridge:
        base_amt, base_unit = _to_base(item["amount"], item["unit"])
        inventory[item["name"].lower()] = {
            "base_amount": base_amt,
            "base_unit": base_unit,
            "original_unit": item["unit"],
            "display_name": item["name"],
            "original_amount": item["amount"],
        }

    shortages = []

    for day_str in sorted(meal_plan.keys()):
        recipe = recipe_map.get(meal_plan[day_str])
        if not recipe:
            continue
        for ing in recipe["ingredients"]:
            key = ing["name"].lower()
            n_base, n_base_unit = _to_base(ing["amount"], ing["unit"])

            if key not in inventory:
                shortages.append({
                    "name": ing["name"],
                    "need_amount": ing["amount"],
                    "need_unit": ing["unit"],
                    "have_amount": 0,
                    "have_unit": ing["unit"],
                    "runs_out_on": day_str,
                    "recipe": recipe["name"],
                })
                continue

            item = inventory[key]
            if item["base_unit"] != n_base_unit:
                continue  # incomparable — skip

            before = item["base_amount"]
            item["base_amount"] = max(0, item["base_amount"] - n_base)

            if before < n_base:  # had less than needed
                shortages.append({
                    "name": item["display_name"],
                    "need_amount": ing["amount"],
                    "need_unit": ing["unit"],
                    "have_amount": round(_from_base(before, item["original_unit"]), 3),
                    "have_unit": item["original_unit"],
                    "runs_out_on": day_str,
                    "recipe": recipe["name"],
                })

    if not shortages:
        return {"fully_covered": True, "shop_by": None, "items": []}

    earliest = min(s["runs_out_on"] for s in shortages)
    shop_by = (date.fromisoformat(earliest) - timedelta(days=1)).isoformat()

    return {"fully_covered": False, "shop_by": shop_by, "items": shortages}


def get_forgotten_ingredients():
    """Return fridge ingredients not used in any saved recipe."""
    fridge = get_ingredients()
    recipes = get_recipes()

    recipe_ingredient_names = set()
    for recipe in recipes:
        for ing in recipe["ingredients"]:
            recipe_ingredient_names.add(ing["name"].lower())

    return [ing for ing in fridge if ing["name"].lower() not in recipe_ingredient_names]
