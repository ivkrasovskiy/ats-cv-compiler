import { test, expect } from '@playwright/test'

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('shows the app title in nav', async ({ page }) => {
    await expect(page.locator('header')).toContainText('ats-cv-compiler')
  })

  test('shows Quick Start section', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Quick Start' })).toBeVisible()
  })

  test('has Build Generic CV card', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Build Generic CV' })).toBeVisible()
  })

  test('has System Status collapsible section', async ({ page }) => {
    await expect(page.getByText('System Status')).toBeVisible()
  })

  test('all nav links are visible', async ({ page }) => {
    for (const label of ['Dashboard', 'Profile', 'Target Jobs', 'Gen Config', 'Generated CVs']) {
      await expect(page.getByRole('link', { name: label })).toBeVisible()
    }
  })

  test('shows Getting Started section on first load', async ({ page }) => {
    await page.evaluate(() => localStorage.removeItem('ats_onboarded'))
    await page.reload()
    await expect(page.getByText('Getting Started')).toBeVisible()
  })
})
