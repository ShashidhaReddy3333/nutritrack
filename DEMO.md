# NutriTrack Demo Walkthrough

This guide uses the local development stack. Production uses `docker-compose.yml` and must not use demo credentials.

## Start Local Demo

```bash
cp .env.development.example .env
docker compose -f docker-compose.dev.yml up --build
```

Open `http://localhost:5173`. The backend runs migrations, seeds the demo account, and exposes the API at `http://localhost:8000`.

## Demo Credentials

| Email | Password |
|---|---|
| demo@nutritrack.app | `SEED_DEMO_PASSWORD` or `nutritrack-dev-only-change-me` |

## Walkthrough

1. Register a new account or sign in with the demo account.
2. Complete profile setup. The browser timezone is saved to the profile so daily and weekly meal totals use local day boundaries.
3. Add products from the Products page. Uploads are capped by size, page count, page dimensions, and extraction timeout; manual product entry is available.
4. Log a meal from saved products or parse a natural-language meal description through the configured Ollama-compatible endpoint.
5. Review Dashboard and History. History loads older meals by page instead of silently stopping at API defaults.
6. Open Profile to export account data or permanently delete the account.

Auth is cookie-only for browser flows. Login, register, and refresh set httpOnly cookies and return session/user metadata, not bearer tokens.
