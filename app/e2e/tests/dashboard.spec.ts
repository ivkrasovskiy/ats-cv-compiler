import { test, expect } from '@playwright/test'

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('shows the app title in nav', async ({ page }) => {
    await expect(page.locator('header')).toContainText('ats-cv-compiler')
  })

  test('shows System Status section', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'System Status' })).toBeVisible()
  })

  test('shows Quick Actions section', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Quick Actions' })).toBeVisible()
  })

  test('has Build Generic CV button', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Build Generic CV' })).toBeVisible()
  })

  test('navigates to Build page from button', async ({ page }) => {
    await page.getByRole('button', { name: 'Build Generic CV' }).click()
    await expect(page).toHaveURL('/build')
  })

  test('all nav links are visible', async ({ page }) => {
    for (const label of ['Dashboard', 'Data', 'Jobs', 'Build', 'Output']) {
      await expect(page.getByRole('link', { name: label })).toBeVisible()
    }
  })
})
