# CoPantry — Development Journal

A running log of every development session: what was built, why, and what changed.

---

## v1 — Initial Scaffolding · 2026-02-23

**Focus:** Get something working end to end.

Core scaffolding built from scratch: ingredient tracking, recipe storage, AI-powered recipe suggestions, a basic meal planner, and a shopping list. The goal was to have a live, usable app as a foundation to iterate on. Deployed to Streamlit Community Cloud with seeded demo data so anyone could explore it immediately without setup.

**What shipped:**
- Ingredient tracking (name, amount, unit)
- Recipe storage (manual entry)
- AI suggestions: what can I cook with what I have?
- Basic meal planner
- Shopping list

---

## v2 — AI Recipe Extraction · 2026-02-24

**Focus:** Make it easy to get recipes into the app.

Manually entering every recipe was too slow. Added support for uploading a photo or PDF and having AI extract the details automatically. Recognised that many physical recipe cards (like HelloFresh cards) have ingredients on the front and steps on the back, so added support for uploading two images together and PDFs with multiple pages. The AI combines content across pages into a single recipe.

**What shipped:**
- Photo-based recipe extraction via Gemini AI
- PDF recipe extraction
- Multi-page recipe card support (front and back)
- Note in UI: upload one recipe at a time to avoid mixing content across recipes

---

## v3 — Meaningful Units · 2026-02-24

**Focus:** Fix ingredient data quality.

Two problems surfaced from real use. First, the default unit was "pieces" for anything uncategorised, so a recipe might say "4 pieces of tomatoes" — ambiguous and unhelpful. Replaced with a structured set of natural measurements: whole, half, quarter, slice, clove, head, bunch, sprig, leaf, grams, oz, ml, cups, tablespoons, teaspoons, can, jar, bag, box, piece. Second, when AI couldn't confidently read an amount or unit from a photo, it was silently defaulting to `1` and `pieces`. Changed this so unknown fields return null and are flagged for the user to fill in before saving.

**What shipped:**
- Natural unit system replacing generic defaults
- Unknown fields flagged for user confirmation (null instead of silent guess)
- Updated AI extraction prompt to use the structured unit list

---

## v4 — Home Dashboard · 2026-02-24

**Focus:** Give the app a useful starting point.

Added a Home page with KPI metrics, an AI-generated daily insight, cooking history, and forgotten ingredient tracking. Cached the AI insight in session state so it doesn't regenerate on every Streamlit rerun — only when explicitly refreshed.

**What shipped:**
- Home dashboard with key metrics
- AI daily insights (cached in session state)
- Cooking history tracking
- Forgotten ingredient detection: ingredients in the pantry not used in any saved recipe

---

## v5 — Editing · 2026-02-24

**Focus:** Fix the obvious gap: what if you entered something wrong?

Added the ability to edit recipes and update ingredient amounts after they've been saved. Small quality-of-life improvement but important for day-to-day use.

**What shipped:**
- Recipe editing
- Ingredient amount editing

---

## v6 — Discovery Pages · 2026-02-24

**Focus:** Help new visitors understand what the app is.

Added a Getting Started guide, a Feedback page with a Google Form link, and an About page with the full product narrative covering the problem, solution, design decisions, and how it was built.

**What shipped:**
- Getting Started page
- Feedback page
- About page (full product story)

---

## v7 — Calendar Meal Planner · 2026-02-24

**Focus:** Make meal planning concrete and time-bound.

Replaced the basic meal planner with a proper 7-day calendar view. Each day shows breakfast, lunch, and dinner slots. Added "Eating Out" and "Vacation / Skip" as special options alongside saved recipes. Added an AI fill feature for unplanned days that picks from saved recipes and avoids repeating the same recipe on consecutive days.

**What shipped:**
- 7-day calendar view starting from today
- Breakfast, lunch, dinner slots per day
- Eating Out and Vacation / Skip options
- AI fill for unplanned days
- Week navigation (previous/next week)

---

## v8 — Quantity-Aware Ingredient System · 2026-02-24

**Focus:** Make the app actually know if you have enough of something.

Early cookability logic only checked ingredient names — if "eggs" were in the pantry, a recipe was considered makeable regardless of quantity. Replaced with real quantity math: unit conversion between compatible units (grams/oz, cups/ml, etc.) and a check against actual available amounts. Marking a recipe as cooked automatically deducts the exact amounts used. The meal planner's shopping plan now projects ingredient depletion day by day and tells you the specific date you need to shop and exactly what to buy.

**What shipped:**
- Unit conversion engine (grams/oz, cups/ml, tablespoons/teaspoons, etc.)
- Quantity-aware cookability check
- Automatic pantry deduction when recipe is marked as cooked
- Meal planner shopping projection: specific shop-by date, exact items needed

---

## v9 — Pantry Storage and Ingredient Metadata · 2026-02-24

**Focus:** Track more about each ingredient.

Renamed "Fridge" to "Pantry" throughout the app to better reflect the full home ingredient inventory (not just refrigerated items). Added AI-generated per-ingredient storage tips. Added date tracking: when each ingredient was added and last updated. Added column headers to the ingredient table.

**What shipped:**
- Renamed Fridge → Pantry throughout
- AI-generated per-ingredient storage tips
- Added date and last updated timestamps on ingredients
- Column headers on ingredient table

---

## v10 — Ingredient Location Tagging + Meal Planning Depth · 2026-02-24

**Focus:** Enable location-aware features, especially thaw reminders.

Added explicit storage location tagging (Fridge, Freezer, Pantry, Other) for each ingredient. This unlocked a class of features that weren't possible before — most importantly, automatic thaw reminders: if tomorrow's dinner uses chicken breast tagged as Freezer, the app now knows to remind you tonight. No AI needed; the logic is deterministic.

Redesigned the Home page from a metrics dashboard into a daily morning briefing: today's meals, thaw reminders, and shopping deadlines front and center. Expanded the meal planner to support breakfast, lunch, and dinner for every day, with the meal plan persisted to the database.

**What shipped:**
- Ingredient location tagging: Fridge, Freezer, Pantry, Other
- Automatic thaw reminders on Home page
- Home page redesigned as daily briefing (Today / What to Do Today / This Week)
- Breakfast, lunch, dinner meal planning (3 meals/day)
- Meal plan persisted to SQLite

---

## v11 — Rebrand and Polish · 2026-02-24

**Focus:** Sharpen the identity and clean up rough edges.

Rebranded the app to CoPantry. Fixed lingering "fridge" references throughout. Underlined content links for clarity. Updated the Getting Started page with clickable internal page links.

**What shipped:**
- Rebranded to CoPantry
- Fixed fridge → pantry references across all pages
- Underlined content links
- Getting Started updated with clickable page links

---

## v12 — Home as Landing Page + Seed Data + Polish · 2026-02-26

**Focus:** Restructure navigation and prepare the app for external visitors.

Reordered the sidebar so Home is the landing page. Expanded seed data with more ingredients, four new recipes, and a full 7-day pre-populated meal plan so visitors land in a fully usable demo. Added quick-action "Eating Out" buttons directly on the Home page so users can log today's meals without going to the planner. Cohesive page restructure across Shopping List, Suggestions, Recipes, and Meal Planner. Added a grocery trip recommendation and AI-powered reschedule feature to the Meal Planner.

**What shipped:**
- Home reordered to be the app's landing page
- Expanded seed data: more ingredients, 4 new recipes, full 7-day meal plan
- "Eating Out" quick-action buttons on Home for today's meals with undo support
- Grocery trip recommendation on Meal Planner (specific shop-by date + item count)
- "Reschedule with AI" feature: user inputs their available grocery date, AI rearranges the meal plan so pre-shopping days only use pantry ingredients
- Smarter recipe sorting in Meal Planner: most-cooked recipes appear first
- Color-highlighted ingredients (blue) and dates (orange) in Home reminders
- Page restructure for consistency across Suggestions, Recipes, Shopping List
- Dev Container configuration added

---

## Session — 2026-03-26

**Focus:** AI cost controls, pantry UX overhaul, expiry date tracking, and visitor onboarding.

A broad session covering multiple distinct areas. Driven by a combination of deployment concerns (protecting against unexpected AI costs), practical UX issues noticed from real use, and preparing the app for external visitors reviewing it as a portfolio piece.

### AI Usage Quota

Added a global daily cap of 50 AI calls shared across all visitors. This protects against runaway API costs while still giving a small number of visitors full access to every feature in a day.

- New `ai_usage` table in SQLite, keyed by date
- `check_and_increment_quota(limit)` function: atomic check-and-increment, returns False if limit is reached
- `show_ai_limit_message()` in utils: shows a toast notification and an inline warning explaining the limit and that it resets daily
- Sidebar AI usage counter on every page: shows current usage, total limit, and remaining calls with a green/yellow/red indicator
- All AI-triggered buttons across Pantry, Recipes, Suggestions, Meal Planner, and Home now check the quota before calling Gemini

### Pantry Page Overhaul

The existing add-ingredient form was a single row using `st.form`. Replaced it entirely with a session-state-driven dynamic multi-row interface. Several non-trivial Streamlit constraints had to be worked around.

**Dynamic multi-row add:**
- Rows tracked by IDs in session state (`add_row_ids`, `add_row_counter`)
- Each row has: name, amount, unit, location, expiry (optional), and a remove button
- "Add Row" button appends a new row without submitting the form
- A "pending key" pattern was used to pre-populate location dropdowns after AI suggestions, working around Streamlit's restriction on modifying widget session state keys after instantiation

**Bulk AI location suggestion:**
- Single "Suggest Locations" button sends all named rows to Gemini in one API call
- Suggested locations are applied to all rows at once; storage tips appear inline below each row
- Storage tips no longer generate on page load (were generating on every Streamlit rerun)

**Duplicate detection:**
- On save, each ingredient name is checked case-insensitively against the database
- If a duplicate is found, a `st.dialog` modal shows the conflict with current and new amounts
- User chooses: "Combine amounts" (same unit: sum the amounts; different unit: add as separate entry) or "Add as separate entries"

**Other pantry changes:**
- Ingredient names auto title-cased at the database layer on save
- "Date" column renamed to "Added Date"
- Column widths adjusted to prevent Edit/Remove buttons being pushed off-screen
- CSS applied to reduce Edit/Remove button height to match surrounding content
- Edit form expanded to include expiry date field (alongside amount and location)
- "Clear All" button added with a `st.dialog` confirmation step

### Expiry Date Tracking

Added optional expiry date tracking for ingredients. Expiry dates are color-coded throughout:
- Red: expired or expiring today
- Orange: expiring tomorrow
- Amber: expiring in 2-3 days
- Plain text: further out

**Home page warnings:**
- `get_expiring_soon_ingredients(days=3)` surfaces items expiring within 3 days
- Expired items: red error callout
- Expiring today: red error callout
- Expiring tomorrow: yellow warning callout
- Expiring in 2-3 days: blue info callout

**AI meal suggestions:**
- Meal Planner's "Fill Unplanned Days with AI" now passes ingredients expiring within 7 days to the Gemini prompt, biasing suggestions toward recipes that use those ingredients

### Visitor Onboarding Banner

Added a welcome banner to the Home page to give context to new visitors (primarily recruiters and hiring teams). The banner is a styled HTML div with a blue left border. Three quick links below it: Getting Started, About, and Feedback.

Design constraints applied to the banner:
- No em-dashes anywhere in the text (project-wide policy: em-dashes signal AI-generated content)
- Kept to 3 lines to avoid awkward word wrapping
- Feedback link included as part of the text, not just as a standalone link

### Em-Dash Policy

Identified and removed all em-dashes from user-visible narrative text across the app. Em-dashes in Streamlit widget labels or code comments are acceptable; the concern is with prose that visitors read.

Files updated:
- `pages/8_About.py`: tagline, problem description (3 instances)
- `utils.py`: AI limit toast message and inline warning
- `pages/7_Feedback.py`: opening paragraph

**Rule:** Replace em-dashes in narrative prose with a period (split into two sentences) or a colon/comma where a pause or list introduction is intended.

### Other Fixes
- Pantry ingredient column width reduced to prevent layout overflow
- Getting Started page link label shortened to fit within Streamlit's truncation limit
- About page: removed a line that read "I built this to solve a real problem I had" (felt on-the-nose)
- Meal Planner: fixed indentation bug in the reschedule block introduced during an earlier edit
- Inline date picker added under Home's "Today" heading so users can correct for timezone differences

---

*Last updated: 2026-03-26*
