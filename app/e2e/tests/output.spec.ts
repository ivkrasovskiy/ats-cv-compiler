import { test, expect } from '@playwright/test'

test.describe('Generated CVs', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/output')
  })

  test('page loads without Vite errors', async ({ page }) => {
    // If OutputPage.tsx has a syntax error, Vite injects an overlay containing '[plugin:vite:'
    // This test fails fast and clearly when the page module is broken.
    await expect(page.getByText('[plugin:vite:')).not.toBeVisible({ timeout: 3_000 })
    // The heading must be present — proves the React component tree mounted successfully
    await expect(page.getByText('Generated CVs')).toBeVisible({ timeout: 5_000 })
  })

  test('shows Generated CVs panel heading', async ({ page }) => {
    await expect(page.getByText('Generated CVs')).toBeVisible({ timeout: 5_000 })
  })

  test('shows empty state or file list', async ({ page }) => {
    // Either shows the empty message or the file list panel
    const emptyMsg = page.getByText('No output files yet')
    const panel = page.locator('.overflow-hidden.rounded-xl')
    await expect(emptyMsg.or(panel)).toBeVisible({ timeout: 5_000 })
  })

  test('shows editor placeholder when no file selected', async ({ page }) => {
    await expect(page.getByText('Click a file name to preview its PDF.')).toBeVisible()
  })
})
