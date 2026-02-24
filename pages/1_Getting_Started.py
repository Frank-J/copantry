import streamlit as st
from utils import apply_sidebar_style

st.set_page_config(page_title="Getting Started", page_icon="🚀", layout="wide")
apply_sidebar_style()

st.title("🚀 Getting Started")
st.markdown("New here? This page walks you through everything the app can do and how to use it effectively.")

st.divider()

st.markdown("""
## Your Workflow

The app is built around a simple loop:

**Add ingredients → Save recipes → Get suggestions → Cook → Repeat**

Each part of the app plays a role in that cycle. Here's how to use each one.
""")

st.divider()

st.markdown("## Step-by-Step Guide")

# Step 1
st.markdown("""
### 🥫 1. Set Up Your Pantry

Log everything you currently have at home — fridge, freezer, and dry goods. Be as specific as you can about amounts and location — this is what drives recipe suggestions, cookability checks, and your shopping plan.

**Tips:**
- Use the unit dropdown to pick the most natural measurement (e.g. *whole* for tomatoes, *grams* for meat, *clove* for garlic)
- Tag each ingredient's location (Fridge, Freezer, Pantry) — the Home page uses this to remind you when to thaw things
- Storage tips are shown for each ingredient so you know where to keep things and how long they last
- Marking a recipe as cooked automatically deducts the ingredients from your pantry
- The Home dashboard will flag any ingredients that aren't in any of your saved recipes — those are your most at-risk items for waste
""")
st.page_link("pages/3_Pantry.py", label="Go to Pantry →")

st.markdown("---")

# Step 2
st.markdown("""
### 📖 2. Add Your Recipes

You can save recipes in two ways:

**📷 Photo or PDF upload**
Take a photo of a recipe card, or upload a PDF. The AI reads the name, ingredients, cooking time, and instructions automatically.
- For recipes that span two sides (like HelloFresh cards), upload both the front and back together
- Always upload one recipe at a time — mixing multiple recipes in one upload will produce unreliable results
- Review what the AI extracted before saving — any fields it couldn't read will be clearly flagged for you to fill in

**✏️ Manual entry**
Type the recipe details directly. Add ingredients one per line in the format: `Name, Amount, Unit`
(e.g. `Chicken Breast, 500, grams`)
""")
st.page_link("pages/4_Recipes.py", label="Go to Recipes →")

st.markdown("---")

# Step 3
st.markdown("""
### 💡 3. Get Recipe Suggestions

Click the button to see what you can cook. The AI looks at your current fridge contents and tells you:
- Which of your saved recipes you can make right now
- New recipe ideas based on what you have, even if they're not saved yet
""")
st.page_link("pages/5_Suggestions.py", label="Go to Suggestions →")

st.markdown("---")

# Step 4
st.markdown("""
### 📅 4. Plan Your Meals

Plan breakfast, lunch, and dinner for each day of the week. Changes are saved automatically. You can also use AI to fill in any unplanned days.
""")
st.page_link("pages/6_Meal_Planner.py", label="Go to Meal Planner →")

st.markdown("---")

# Step 5
st.markdown("""
### 🛒 5. Build a Shopping List

Pick a recipe and the AI compares what it needs against what's in your pantry — telling you exactly what to buy and how much.
""")
st.page_link("pages/7_Shopping_List.py", label="Go to Shopping List →")

st.markdown("---")

# Step 6
st.markdown("""
### ✅ 6. Log What You Cook

Hit the **✅ Cooked** button after making a meal. Over time this builds your cooking history, which powers the *Most Cooked Recipes* and *Most Used Ingredients* stats on the Home dashboard.
""")
st.page_link("pages/4_Recipes.py", label="Go to Recipes →")

st.markdown("---")

# Step 7
st.markdown("""
### 🏠 7. Check Your Dashboard

Open the app each morning to see your daily briefing:
- Today's planned breakfast, lunch, and dinner
- Thaw reminders if any frozen ingredients are needed in the next day or two
- Shopping deadline and what you'll run short on
- A 7-day week view so you can spot gaps and plan ahead
""")
st.page_link("pages/2_Home.py", label="Go to Home →")

st.divider()

st.markdown("""
## A Note on AI Features

The Suggestions, Meal Planner, Shopping List, Home insights, and recipe photo extraction all use **Google's Gemini AI**. A few things worth knowing:

- AI responses may vary slightly between sessions — this is normal
- The quality of suggestions improves as you add more ingredients and recipes
- Home insights are generated once when you first visit the page each session. Use the **Refresh Insight** button if your fridge contents have changed
""")
