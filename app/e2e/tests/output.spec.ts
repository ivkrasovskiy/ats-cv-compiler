import { test, expect } from '@playwright/test'

test.describe('Generated CVs', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/output')
  })

  test('shows Generated CVs panel heading', async ({ page }) => {
    await expect(page.getByText('Generated CVs')).toBeVisible()
  })

  test('shows empty state or file list', async ({ page }) => {
    // Either shows the empty message or the file list panel
    const emptyMsg = page.getByText('No output files yet')
    const panel = page.locator('.overflow-hidden.rounded-xl')
    await expect(emptyMsg.or(panel)).toBeVisible({ timeout: 5_000 })
  })

  test('shows editor placeholder when no MD selected', async ({ page }) => {
    await expect(page.getByText('Select "Edit MD" to edit')).toBeVisible()
  })
})
