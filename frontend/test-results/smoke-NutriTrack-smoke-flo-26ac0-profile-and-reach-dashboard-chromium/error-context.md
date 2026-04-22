# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: smoke.spec.ts >> NutriTrack smoke flows >> user can register, set up profile, and reach dashboard
- Location: tests\e2e\smoke.spec.ts:4:3

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://127.0.0.1:5173/register
Call log:
  - navigating to "http://127.0.0.1:5173/register", waiting until "load"

```

# Test source

```ts
  1  | import { expect, test } from '@playwright/test'
  2  | 
  3  | test.describe('NutriTrack smoke flows', () => {
  4  |   test('user can register, set up profile, and reach dashboard', async ({ page }) => {
  5  |     const email = `smoke-${Date.now()}@example.com`
  6  | 
> 7  |     await page.goto('/register')
     |                ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://127.0.0.1:5173/register
  8  |     await page.getByLabel('Email address').fill(email)
  9  |     await page.getByLabel('Password', { exact: true }).fill('smoketest123')
  10 |     await page.getByLabel('Confirm password').fill('smoketest123')
  11 |     await page.getByRole('button', { name: 'Create account' }).click()
  12 | 
  13 |     await expect(page).toHaveURL(/\/profile\/setup$/)
  14 | 
  15 |     await page.getByLabel('Age').fill('30')
  16 |     await page.getByLabel('Weight (kg)').fill('80')
  17 |     await page.getByLabel('Height (cm)').fill('180')
  18 |     await page.getByRole('button', { name: /Continue/ }).click()
  19 |     await page.getByRole('button', { name: 'Calculate my targets' }).click()
  20 | 
  21 |     await expect(page).toHaveURL(/\/dashboard$/)
  22 |     await expect(page.getByText("Today's Meals")).toBeVisible()
  23 |   })
  24 | 
  25 |   test('demo user can log in and see seeded products', async ({ page }) => {
  26 |     await page.goto('/login')
  27 |     await page.getByLabel('Email address').fill('demo@nutritrack.app')
  28 |     await page.getByLabel('Password').fill('nutritrack123')
  29 |     await page.getByRole('button', { name: 'Sign in' }).click()
  30 | 
  31 |     await expect(page).toHaveURL(/\/dashboard$/)
  32 | 
  33 |     await page.goto('/products')
  34 | 
  35 |     await expect(page.getByText('Optimum Nutrition Gold Standard Whey')).toBeVisible()
  36 |     await expect(page.getByText('Quaker Old Fashioned Oats')).toBeVisible()
  37 |     await expect(page.getByText('Almond Butter (Natural)')).toBeVisible()
  38 |   })
  39 | })
  40 | 
```