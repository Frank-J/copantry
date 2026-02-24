import streamlit as st
from database import initialize_db
from utils import apply_sidebar_style

initialize_db()

st.set_page_config(
    page_title="Fridge & Recipe Manager",
    page_icon="🍳",
    layout="wide",
)
apply_sidebar_style()

st.title("🍳 Fridge & Recipe Manager")
st.markdown("*An AI-powered tool for smarter ingredient management and meal planning.*")

st.divider()

st.markdown("""
## The Problem

When I first moved to Seattle to start living and working on my own, I began buying groceries and cooking for myself for the first time. I quickly ran into a recurring frustration: recipes often called for only a small portion of what I had purchased — one tablespoon of cornstarch, half a head of lettuce, a splash of fish sauce. The rest would sit in the fridge, get forgotten, and eventually go to waste.

Over time, I switched to **HelloFresh** to solve this. Ingredients come pre-measured, portioned exactly for each recipe — no leftovers, no waste, no guesswork. It worked, but it came at a cost. Buying and cooking with your own groceries is significantly more affordable, and I wanted to get back to that without the waste and disorganization that came with it.

What I needed was something that could act as both an **inventory system** and a **cooking advisor** — something that knew what I had, helped me use it efficiently, and guided me toward meals I could actually make.

## The Solution

Fridge & Recipe Manager is that web app. It gives you:

- **Pantry tracking** — log everything you have at home with amounts, units, and location (Fridge/Freezer/Pantry/Other), enabling automatic thaw reminders
- **Recipe storage** — save recipes manually or by uploading a photo or PDF, with AI extracting the details automatically
- **AI-powered suggestions** — find out what you can cook with what you already have
- **Calendar meal planning** — plan breakfast, lunch, and dinner for each day of the week, with eating out and vacation options built in
- **Smart shopping plan** — projects when you'll run out of each ingredient and tells you the specific day to shop and exactly what to buy

The goal is to make home cooking feel as frictionless as a meal kit service, without the price tag.

## How I Built It

This web app was built in under a week as part of my APM application. Rather than starting from a blank editor, I used **Claude Code** — an AI coding assistant — to help design the architecture, write the code, and debug issues in real time.

This wasn't just about moving faster. It was about thinking through product decisions under a real deadline: what features matter most for an MVP, how to handle data storage for both personal and demo use cases, and how to deploy something shareable quickly. Claude Code acted as a technical collaborator, letting me stay focused on the product thinking while it helped with implementation.

**Tech stack:** Python · Streamlit · Google Gemini AI · SQLite · Deployed on Streamlit Community Cloud

## Challenges Along the Way

No project goes exactly to plan. A few real obstacles I navigated:

- **AI API setup**: Getting the Gemini API working required debugging quota issues, deprecated model versions, and billing configuration — a good reminder that third-party integrations always carry risk and require flexibility
- **Local vs. deployed data**: I needed the app to work as both a personal daily tool (with persistent data on my laptop) and a shareable demo (accessible via URL without any setup). The solution was pre-seeding the deployed version with sample data so anyone can explore it immediately

## Design Decisions

Building a working product in a short timeframe means making deliberate trade-offs. Here are a few worth highlighting:

**Meaningful units over generic defaults**
The first version defaulted to "pieces" for anything it couldn't categorise — so a recipe might call for "4 pieces of tomatoes." That's ambiguous and unhelpful. I replaced the generic unit list with a structured set of natural measurements (whole, half, quarter, slice, clove, head, bunch, etc.) and updated the AI extraction prompt to use them. The result is ingredient data that actually reflects how people cook.

**User confirmation over AI guessing**
When extracting a recipe from a photo or PDF, the AI sometimes can't confidently read an amount or unit. The original approach silently defaulted to `1` and `pieces`. I changed this so unknown fields return null and are flagged for the user to fill in before saving. Bad data is worse than missing data — and asking the user takes two seconds.

**Multi-page recipe support**
Most recipe apps assume a recipe fits on one image. HelloFresh cards and many cookbooks put ingredients on the front and steps on the back. Recognising this as a real gap, I added support for uploading two images together (front and back) as well as PDFs, with the AI combining content across pages into a single recipe. A note in the UI explains to upload one recipe at a time to avoid mixing content across recipes.

**Pantry over fridge**
Calling the inventory section "Fridge" was a quick early decision that turned out to be wrong — not everything people track is refrigerated. Garlic, pasta, canned goods, and spices live in the pantry or cupboard. Renaming it to "Pantry" is a small change on the surface but reflects a more accurate mental model of what the app is actually managing: your full home ingredient inventory, not just what's cold.

**Local tool and shareable demo from the same codebase**
The app serves two purposes: a personal pantry management tool I actually use, and a shareable portfolio demo. Rather than building two versions, the same codebase runs locally with a persistent SQLite database and on Streamlit Cloud with pre-seeded sample data — so reviewers can explore it immediately without any setup.

**Ingredient location tagging**
Early versions tracked what you had but not where it was stored. Adding Fridge/Freezer/Pantry/Other as an explicit field enables a class of features that wouldn't otherwise be possible — most importantly, automatic thaw reminders. If tomorrow's dinner recipe uses chicken breast tagged as Freezer, the app knows to remind you tonight. No AI needed; the reminder is deterministic.

**Home page as a daily briefing**
The original Home page was a dashboard of numbers — how many ingredients, how many recipes. Useful as a reference, but not actionable. The redesign reframes it around three questions a person actually asks in the morning: what am I doing today, what do I need to do ahead of time, and what do I need to plan for. The page now surfaces today's meals, thaw reminders, and shopping deadlines — the things that require action — front and center.

**Cached AI insights**
The Home dashboard generates an AI insight on first load. Rather than regenerating it on every page interaction (Streamlit reruns the entire script on any click), the insight is cached in session state and refreshed only when explicitly requested. This keeps the experience fast and avoids unnecessary API calls.

**Quantity-aware ingredient tracking**
The first version of cookability checking only looked at ingredient names — if "eggs" were in the fridge, the recipe was considered makeable regardless of how many were left. I replaced this with real quantity math: the app now converts between compatible units (grams ↔ oz, cups ↔ ml, etc.) and checks whether you actually have enough. Marking a recipe as cooked automatically deducts the exact amounts used. The meal planner's shopping plan projects this depletion day by day and tells you the specific date you need to shop and exactly what to buy.

## What I'd Build Next

1. **Native mobile app** — the biggest friction point right now is updating the fridge on the go: you've just bought groceries, you're standing in the kitchen, and opening a web app on a laptop is an extra step. A mobile-first version with a quick-add flow, receipt scanning, and barcode scanning for pantry items would make the experience seamless in everyday use
2. **Expiry date tracking** — alert when ingredients are approaching their use-by date to further reduce waste
3. **Nutritional information** — surface calorie and macro data alongside recipes
4. **Grocery delivery integration** — connect the shopping list directly to Instacart or Amazon Fresh for one-click ordering
""")

st.divider()

with st.expander("📋 Changelog"):
    st.markdown("""
| Version | Changes |
|---|---|
| v10 | Ingredient location tagging (Fridge/Freezer/Pantry/Other); breakfast/lunch/dinner meal planning; persistent meal plan saved to database; Home page redesigned as daily morning briefing with today's meals, thaw reminders, and shopping deadlines |
| v9 | Renamed Fridge to Pantry to better reflect full ingredient inventory; AI-generated per-ingredient storage tips; date added and last updated tracking; column headers on ingredient table |
| v8 | Quantity-aware ingredient system: unit conversion (grams ↔ oz, cups ↔ ml, etc.), automatic pantry deduction when a recipe is marked as cooked, meal plan shopping projection with a specific shop-by date |
| v7 | Calendar meal planner: 7-day forward view starting from today, per-day selectors with eating out and vacation options, AI fill for unplanned days |
| v6 | Getting Started guide, Feedback page, About page with full product narrative |
| v5 | Recipe editing and ingredient amount editing |
| v4 | Home dashboard with KPI metrics, AI daily insights, cooking history, and forgotten ingredient tracking |
| v3 | Natural unit system (whole, clove, head, etc.) replacing generic defaults; unknown fields flagged for user input rather than silently guessed |
| v2 | Photo and PDF recipe extraction via AI; multi-page recipe card support (front and back) |
| v1 | Core scaffolding: ingredient tracking, recipe storage, AI suggestions, basic meal planner, shopping list |
""")

st.caption("Use the sidebar to explore the app.")
