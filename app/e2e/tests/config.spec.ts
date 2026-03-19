import { test, expect } from '@playwright/test'

test.describe('Gen Config', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/build')
  })

  test('shows Gen Config heading', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Gen Config' })).toBeVisible()
  })

  test('shows Content Quality section', async ({ page }) => {
    await expect(page.getByText('Content Quality')).toBeVisible()
  })

  test('shows Save Settings button', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Save Settings' })).toBeVisible()
  })

  test('shows Advanced LLM Connection section', async ({ page }) => {
    await expect(page.getByText('Advanced – LLM Connection')).toBeVisible()
  })

  test('shows Prompts section', async ({ page }) => {
    await expect(page.getByText('Prompts')).toBeVisible()
  })
})
