import sqlite3
import json
from datetime import datetime, timedelta

DB_PATH = "recipes.db"


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

    conn.commit()
    conn.close()


# Ingredient operations

def add_ingredient(name, amount, unit):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO ingredients (name, amount, unit, added_date) VALUES (?, ?, ?, ?)",
        (name, amount, unit, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_ingredients():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, amount, unit, added_date FROM ingredients ORDER BY name")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "amount": r[2], "unit": r[3], "added_date": r[4]} for r in rows]


def delete_ingredient(ingredient_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM ingredients WHERE id = ?", (ingredient_id,))
    conn.commit()
    conn.close()


def update_ingredient_amount(ingredient_id, amount):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE ingredients SET amount = ? WHERE id = ?", (amount, ingredient_id))
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
    """Return recipes where all ingredients are present in the fridge."""
    fridge = get_ingredients()
    recipes = get_recipes()
    fridge_names = {i["name"].lower() for i in fridge}

    cookable = []
    for recipe in recipes:
        recipe_ingredient_names = {i["name"].lower() for i in recipe["ingredients"]}
        if recipe_ingredient_names.issubset(fridge_names):
            cookable.append(recipe)
    return cookable


def get_forgotten_ingredients():
    """Return fridge ingredients not used in any saved recipe."""
    fridge = get_ingredients()
    recipes = get_recipes()

    recipe_ingredient_names = set()
    for recipe in recipes:
        for ing in recipe["ingredients"]:
            recipe_ingredient_names.add(ing["name"].lower())

    return [ing for ing in fridge if ing["name"].lower() not in recipe_ingredient_names]
