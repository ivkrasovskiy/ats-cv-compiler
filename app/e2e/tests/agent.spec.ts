import { test, expect } from '@playwright/test'

test.describe('Agent page', () => {
  test('shows agent terminal page with start button', async ({ page }) => {
    await page.goto('/agent')

    // Heading is visible
    await expect(page.getByRole('heading', { name: 'Agent Terminal' })).toBeVisible()

    // CLI selector exists
    await expect(page.locator('select')).toBeVisible()

    // Start button is present
    await expect(page.getByRole('button', { name: 'Start' })).toBeVisible()

    // Terminal container is in the DOM
    await expect(page.locator('.xterm, [data-testid="terminal-container"]').or(
      page.locator('div').filter({ hasText: 'Select a CLI and click Start to begin.' })
    )).toBeVisible()
  })

  test('nav link to Agent is present', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByRole('link', { name: 'Agent' })).toBeVisible()
  })

  test('clicking Agent nav link navigates to /agent', async ({ page }) => {
    await page.goto('/')
    await page.getByRole('link', { name: 'Agent' }).click()
    await expect(page).toHaveURL('/agent')
  })
})
