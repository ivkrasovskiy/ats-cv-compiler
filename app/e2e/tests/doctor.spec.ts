import { test, expect } from '@playwright/test'

test.describe('Doctor / Lint checks', () => {
  test('dashboard shows doctor status', async ({ page }) => {
    await page.goto('/')
    // Either checks load or error message shown
    await expect(
      page.getByRole('heading', { name: 'System Status' }).or(page.getByText('Could not reach backend')),
    ).toBeVisible()
  })

  test('Run Doctor button triggers a refetch', async ({ page }) => {
    await page.goto('/')
    const btn = page.getByRole('button', { name: 'Run Doctor' })
    await expect(btn).toBeVisible()
    await btn.click()
    // Should not crash — page still shows heading
    await expect(page.getByRole('heading', { name: 'System Status' })).toBeVisible()
  })

  test('Run Lint button triggers lint', async ({ page }) => {
    await page.goto('/')
    await page.getByRole('button', { name: 'Run Lint' }).click()
    // Lint Results section should appear
    await expect(
      page.getByRole('heading', { name: 'Lint Results' }).or(page.getByText('No issues found')).first(),
    ).toBeVisible({ timeout: 10_000 })
  })
})
