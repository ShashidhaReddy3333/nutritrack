import { expect, test } from '@playwright/test'

test.describe('NutriTrack smoke flows', () => {
  test('user can register, set up profile, and reach dashboard', async ({ page }) => {
    const email = `smoke-${Date.now()}@example.com`

    await page.goto('/register')
    await page.getByLabel('Email address').fill(email)
    await page.getByLabel('Password', { exact: true }).fill('smoketest123')
    await page.getByLabel('Confirm password').fill('smoketest123')
    await page.getByRole('button', { name: 'Create account' }).click()

    await expect(page).toHaveURL(/\/profile\/setup$/)

    await page.getByLabel('Age').fill('30')
    await page.getByLabel('Weight (kg)').fill('80')
    await page.getByLabel('Height (cm)').fill('180')
    await page.getByRole('button', { name: /Continue/ }).click()
    await page.getByRole('button', { name: 'Calculate my targets' }).click()

    await expect(page).toHaveURL(/\/dashboard$/)
    await expect(page.getByText("Today's Meals")).toBeVisible()
  })

  test('demo user can log in and see seeded products', async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel('Email address').fill('demo@nutritrack.app')
    await page.getByLabel('Password').fill('nutritrack123')
    await page.getByRole('button', { name: 'Sign in' }).click()

    await expect(page).toHaveURL(/\/dashboard$/)

    await page.goto('/products')

    await expect(page.getByText('Optimum Nutrition Gold Standard Whey')).toBeVisible()
    await expect(page.getByText('Quaker Old Fashioned Oats')).toBeVisible()
    await expect(page.getByText('Almond Butter (Natural)')).toBeVisible()
  })
})
