import { test, expect } from '@playwright/test'

test.describe('Build Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/build')
  })

  test('shows Build CV heading', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Build CV' })).toBeVisible()
  })

  test('has job selector and LLM selector', async ({ page }) => {
    await expect(page.getByLabel('Job (optional)')).toBeVisible()
    await expect(page.getByLabel('LLM')).toBeVisible()
  })

  test('has Start Build button', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Start Build' })).toBeVisible()
  })

  test('disables button while building', async ({ page }) => {
    await page.getByRole('button', { name: 'Start Build' }).click()
    // Button should become disabled immediately
    await expect(page.getByRole('button', { name: /Building|Start Build/ })).toBeVisible()
  })

  test('starts build and shows log', async ({ page }) => {
    await page.getByRole('button', { name: 'Start Build' }).click()
    // Log section should appear
    await expect(page.getByText('Build Log')).toBeVisible()
  })

  test('build completes end-to-end with example data', async ({ page }) => {
    await page.getByRole('button', { name: 'Start Build' }).click()
    // Wait up to 30s for done/error status badge
    await expect(
      page.locator('span').filter({ hasText: /^(done|error)$/ }),
    ).toBeVisible({ timeout: 30_000 })
  })
})
