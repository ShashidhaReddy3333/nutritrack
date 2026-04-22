# NutriTrack — Demo Walkthrough

This guide walks through a complete end-to-end flow: creating an account, uploading a product PDF, logging a meal, and viewing the dashboard.

## Prerequisites

```bash
cp .env.example .env
# Set ANTHROPIC_API_KEY in .env
docker-compose up --build
```

Wait for "Application startup complete" in the backend logs, then open **http://localhost:5173**.

---

## Step 1 — Register & Set Up Profile

1. Navigate to `http://localhost:5173` → redirected to `/login`
2. Click **Sign up** → enter your email and a password (min 8 chars)
3. You're redirected to `/profile/setup` — a 2-step wizard:
   - **Step 1:** Enter age, sex, weight (kg), height (cm)
   - **Step 2:** Pick activity level and goal (maintain / cut / bulk)
4. Click **Calculate my targets** → you land on the Dashboard

**What happened behind the scenes:**
- `POST /api/v1/auth/register` → JWT returned and stored
- `POST /api/v1/profile` → Mifflin-St Jeor BMR calculated, macro targets derived
- `GET /api/v1/profile/targets` returns e.g. `{ calories: 2477, protein_g: 185, carbs_g: 248, fat_g: 83 }`

---

## Step 2 — Upload a Product PDF

1. Click **Products** in the nav
2. Click **↑ Upload PDF** → select a product nutrition label PDF
   - Example: download any protein powder nutrition facts PDF from the web
3. Wait ~3–5s for AI extraction → a **Review Modal** appears showing:
   - Extracted macros with confidence badge (High / Medium / Low)
   - Editable fields for every nutrient
   - Raw text snippet so you can verify
4. Correct any wrong values (e.g. the AI might read "24" as "2.4")
5. Click **Save product** → product appears in your library

**What happened:**
- `POST /api/v1/products/extract` (multipart) → pdfplumber → PyMuPDF → OCR fallback
- Claude `claude-sonnet-4-6` normalises text to strict JSON schema
- `POST /api/v1/products` → stored in Postgres, embedded in Chroma via `all-MiniLM-L6-v2`

> **No PDF?** Click **+ Manual** to add a product by typing values directly.
> The 3 seeded demo products (Whey, Oats, Almond Butter) are already in the library.

---

## Step 3 — Log a Meal

1. Click **Log Meal** in the nav
2. Select meal type (e.g. **Breakfast**)
3. Type a natural-language description:
   ```
   2 scoops whey protein, 1 cup oats, 1 tbsp almond butter
   ```
4. Click **Parse & Match →** (or press Enter)
5. Claude parses the text into `[{item, quantity, unit}]` — then each item is matched against your products via RAG:
   - Green border = high confidence auto-match
   - Yellow border = needs confirmation → click the correct product from top-3 candidates
6. Adjust quantities if needed (e.g. change "1" to "1.5" scoops)
7. Click **Log 3 items →** → you're redirected to the Dashboard

**What happened:**
- `POST /api/v1/meals/parse` → Claude extracted items, Chroma semantic search + Postgres keyword search found candidates
- `POST /api/v1/meals` → nutrients scaled by `quantity_grams / serving_size_g`, stored in `meal_items`

---

## Step 4 — View the Dashboard

Back on the Dashboard you'll see:

**Today tab:**
- **Calorie ring** — consumed vs target, turns red if over goal
- **Macro bars** — protein / carbs / fat progress
- **Micro stats** — fiber, sugar, sodium
- **Meal timeline** — click any meal to expand items; click `×` to delete

**This Week tab:**
- Line chart: calorie trend over 7 days
- Line chart: macro (P/C/F) trends
- Summary table with per-day totals

---

## API Exploration

Visit **http://localhost:8000/docs** for interactive Swagger UI covering all endpoints.

Key flows:
```
POST   /api/v1/auth/register        → create account
POST   /api/v1/auth/login           → get JWT
GET    /api/v1/profile/targets      → effective daily targets
POST   /api/v1/products/extract     → PDF → AI extraction preview
POST   /api/v1/products             → save confirmed product
POST   /api/v1/meals/parse          → NL text → parsed items + candidates
POST   /api/v1/meals                → save meal entry
GET    /api/v1/meals/daily-totals   → today's nutrient totals
GET    /api/v1/meals/weekly-totals  → 7-day history
```

---

## Demo Credentials (pre-seeded)

| Email | Password |
|---|---|
| demo@nutritrack.app | nutritrack123 |

This account already has 3 products (Whey Protein, Oats, Almond Butter) so you can jump straight to Step 3 to test meal logging.
