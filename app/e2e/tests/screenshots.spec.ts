import { test, expect } from '@playwright/test'

/**
 * Screenshot capture for README documentation.
 * Only runs when TAKE_SCREENSHOTS=1 to avoid slowing CI.
 */
test.describe('Documentation Screenshots', () => {
  test.beforeEach(({ }, testInfo) => {
    if (process.env.TAKE_SCREENSHOTS !== '1') {
      testInfo.skip()
      return
    }
  })

  test('Dashboard', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('h1')).toBeVisible()
    await page.screenshot({ path: 'docs/screenshots/dashboard.png', fullPage: false })
  })

  test('DataBrowser - profile', async ({ page }) => {
    await page.goto('/data')
    // Wait for file list to appear
    await page.waitForSelector('[data-testid="file-tree"], .file-tree, nav', { timeout: 5000 }).catch(() => {})
    await page.screenshot({ path: 'docs/screenshots/data-browser.png', fullPage: false })
  })

  test('JobsPage', async ({ page }) => {
    await page.goto('/jobs')
    await page.waitForTimeout(500)
    await page.screenshot({ path: 'docs/screenshots/jobs-page.png', fullPage: false })
  })

  test('OutputPage', async ({ page }) => {
    await page.goto('/output')
    await page.waitForTimeout(500)
    await page.screenshot({ path: 'docs/screenshots/output-page.png', fullPage: false })
  })

  test('BuildPage', async ({ page }) => {
    await page.goto('/')
    await page.waitForTimeout(500)
    await page.screenshot({ path: 'docs/screenshots/build-page.png', fullPage: false })
  })

  test('AgentPage', async ({ page }) => {
    await page.goto('/agent')
    await expect(page.locator('h1')).toBeVisible()
    await page.waitForTimeout(500)
    // Click Start to launch the CLI session
    await page.click('button:has-text("Start")')
    // Wait for WebSocket to connect (status text changes to "Connected")
    await expect(page.locator('text=Connected')).toBeVisible({ timeout: 15000 })
    // Give CLI a moment to print its welcome output into the terminal
    await page.waitForTimeout(3000)
    await page.screenshot({ path: '../../docs/screenshots/agent.png', fullPage: false })
  })
})
