import streamlit as st

st.set_page_config(page_title="Getting Started", page_icon="🚀", layout="wide")

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

st.markdown("""
## Step-by-Step Guide

### 🧊 1. Set Up Your Fridge
Go to the **Fridge** page and log everything you currently have at home. Be as specific as you can about amounts — this is what the AI uses when suggesting what you can cook and what to buy.

**Tips:**
- Use the unit dropdown to pick the most natural measurement (e.g. *whole* for tomatoes, *grams* for meat, *clove* for garlic)
- Update your fridge whenever you buy groceries or use something up
- The Home dashboard will flag any ingredients that aren't in any of your saved recipes — those are your most at-risk items for waste

---

### 📖 2. Add Your Recipes
Go to the **Recipes** page. You can save recipes in two ways:

**📷 Photo or PDF upload**
Take a photo of a recipe card, or upload a PDF. The AI reads the name, ingredients, cooking time, and instructions automatically.
- For recipes that span two sides (like HelloFresh cards), upload both the front and back together
- Always upload one recipe at a time — mixing multiple recipes in one upload will produce unreliable results
- Review what the AI extracted before saving — any fields it couldn't read will be clearly flagged for you to fill in

**✏️ Manual entry**
Type the recipe details directly. Add ingredients one per line in the format: `Name, Amount, Unit`
(e.g. `Chicken Breast, 500, grams`)

---

### 💡 3. Get Recipe Suggestions
Go to the **Suggestions** page and click the button. The AI looks at your current fridge contents and tells you:
- Which of your saved recipes you can make right now
- New recipe ideas based on what you have, even if they're not saved yet

---

### 📅 4. Plan Your Meals
Go to the **Meal Planner** page, choose how many days to plan (3, 5, or 7), and generate a schedule. The AI builds a day-by-day plan using your saved recipes and fills any gaps with simple suggestions.

---

### 🛒 5. Build a Shopping List
Go to the **Shopping List** page and pick a recipe. The AI compares what that recipe needs against what's in your fridge and tells you exactly what to buy — and how much.

---

### ✅ 6. Log What You Cook
On the **Recipes** page, hit the **✅ Cooked** button after making a meal. Over time this builds your cooking history, which powers the *Most Cooked Recipes* and *Most Used Ingredients* stats on the Home dashboard.

---

### 🏠 7. Check Your Dashboard
The **Home** page gives you an at-a-glance overview:
- How many ingredients you have and recipes you've saved
- Which recipes you can make right now with your current fridge
- Ingredients that aren't in any recipe (potential waste)
- AI-generated insights with actionable suggestions for the day
""")

st.divider()

st.markdown("""
## A Note on AI Features

The Suggestions, Meal Planner, Shopping List, Home insights, and recipe photo extraction all use **Google's Gemini AI**. A few things worth knowing:

- AI responses may vary slightly between sessions — this is normal
- The quality of suggestions improves as you add more ingredients and recipes
- Home insights are generated once when you first visit the page each session. Use the **Refresh Insights** button if your fridge contents have changed
""")
