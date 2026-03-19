import { test, expect } from '@playwright/test'

test.describe('Profile (Data Browser)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/data')
  })

  test('shows Profile Data panel heading', async ({ page }) => {
    await expect(page.getByText('Profile Data')).toBeVisible()
  })

  test('shows placeholder when no file selected', async ({ page }) => {
    await expect(page.getByText('Select a file to edit.')).toBeVisible()
  })

  test('shows Profile section', async ({ page }) => {
    await expect(page.getByText('Profile')).toBeVisible()
  })

  test('loads file content when clicked', async ({ page }) => {
    // Click first file button in the tree
    const firstFile = page.locator('details button').first()
    await firstFile.waitFor()
    await firstFile.click()
    // Editor should appear (CodeMirror container)
    await expect(page.locator('.cm-editor')).toBeVisible({ timeout: 5_000 })
  })

  test('shows Save button after selecting a file', async ({ page }) => {
    const firstFile = page.locator('details button').first()
    await firstFile.waitFor()
    await firstFile.click()
    await expect(page.getByRole('button', { name: /Save|Saving/ })).toBeVisible()
  })
})
