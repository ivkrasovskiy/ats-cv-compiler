import { test, expect } from '@playwright/test'

test.describe('Data Browser', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/data')
  })

  test('shows data/ panel heading', async ({ page }) => {
    await expect(page.getByText('data/')).toBeVisible()
  })

  test('shows placeholder when no file selected', async ({ page }) => {
    await expect(page.getByText('Select a file to edit.')).toBeVisible()
  })

  test('loads file content when clicked', async ({ page }) => {
    // Click first file in the tree
    const firstFile = page.locator('ul button').first()
    await firstFile.waitFor()
    await firstFile.click()
    // Editor should appear (CodeMirror container)
    await expect(page.locator('.cm-editor')).toBeVisible({ timeout: 5_000 })
  })

  test('shows Save button after selecting a file', async ({ page }) => {
    const firstFile = page.locator('ul button').first()
    await firstFile.waitFor()
    await firstFile.click()
    await expect(page.getByRole('button', { name: /Save|Saving/ })).toBeVisible()
  })
})
