#!/usr/bin/env node
/**
 * scripts/take_screenshots.mjs
 * Takes screenshots of all 5 app pages using example data.
 *
 * Usage (frontend dev server must already be running on :5173):
 *   node scripts/take_screenshots.mjs
 *
 * Or via the wrapper that handles everything:
 *   bash scripts/run_screenshots.sh
 */

import { chromium } from '../app/e2e/node_modules/playwright/index.mjs'
import { spawn, execSync } from 'child_process'
import { mkdirSync, cpSync, mkdtempSync, rmSync, existsSync } from 'fs'
import { join } from 'path'
import { tmpdir } from 'os'

const FRONTEND_URL = 'http://localhost:5173'
const BACKEND_PORT = 8000
const OUT_DIR = 'docs/screenshots'

async function wait(ms) {
  return new Promise(r => setTimeout(r, ms))
}

async function waitForBackend(maxMs = 20_000) {
  const deadline = Date.now() + maxMs
  while (Date.now() < deadline) {
    try {
      const res = await fetch(`http://localhost:${BACKEND_PORT}/api/health`)
      if (res.ok) return
    } catch { /* not up yet */ }
    await wait(500)
  }
  throw new Error(`Backend did not start within ${maxMs}ms`)
}

async function clickFile(page, text) {
  // FileTree renders plain <button> elements with the file path as text
  const btn = page.locator(`button:has-text("${text}")`).first()
  if (await btn.isVisible().catch(() => false)) {
    await btn.click()
    await wait(800)
    return true
  }
  return false
}

async function main() {
  // ── 1. Set up temp project root with example data ─────────────────────────
  const tmpRoot = mkdtempSync(join(tmpdir(), 'ats-demo-'))
  console.log(`[i] Temp root: ${tmpRoot}`)

  try {
    cpSync('examples/basic/data', join(tmpRoot, 'data'), { recursive: true })
    if (existsSync('examples/basic/jobs')) {
      cpSync('examples/basic/jobs', join(tmpRoot, 'jobs'), { recursive: true })
    } else {
      mkdirSync(join(tmpRoot, 'jobs'), { recursive: true })
    }
    mkdirSync(join(tmpRoot, 'out'), { recursive: true })

    // Pre-build generic CV so the Output page has something to show
    console.log('[…] Pre-building example CV…')
    try {
      execSync(
        `CV_PROJECT_ROOT="${tmpRoot}" uv run cv build --job false`,
        { stdio: 'pipe' }
      )
      console.log('[✓] Example CV built')
    } catch (e) {
      console.warn('[!] Pre-build failed (Output page may be empty):', e.stderr?.toString().slice(0, 200))
    }

    // ── 2. Start backend against tmpRoot ─────────────────────────────────────
    console.log('[…] Starting backend with example data…')
    const backend = spawn(
      'uv', ['run', '--extra', 'app', 'cv-app'],
      {
        env: { ...process.env, CV_PROJECT_ROOT: tmpRoot },
        stdio: 'pipe',
      }
    )
    backend.on('error', e => { throw e })

    try {
      await waitForBackend()
      console.log('[✓] Backend ready')

      mkdirSync(OUT_DIR, { recursive: true })

      const browser = await chromium.launch()
      const ctx = await browser.newContext({
        viewport: { width: 1280, height: 800 },
        colorScheme: 'dark',
      })

      // ── Dashboard ──────────────────────────────────────────────────────────
      {
        const page = await ctx.newPage()
        // Clear onboarding flag so Getting Started checklist is visible
        await page.goto(FRONTEND_URL, { waitUntil: 'networkidle' })
        await page.evaluate(() => localStorage.removeItem('ats_onboarded'))
        await page.reload({ waitUntil: 'networkidle' })
        await wait(600)
        await page.screenshot({ path: `${OUT_DIR}/dashboard.png` })
        await page.close()
        console.log('[✓] dashboard.png')
      }

      // ── Profile editor (open profile.md → shows filled form) ──────────────
      {
        const page = await ctx.newPage()
        await page.goto(`${FRONTEND_URL}/data`, { waitUntil: 'networkidle' })
        await wait(600)
        // Click profile.md in the file tree to open the filled profile form
        await clickFile(page, 'profile.md')
        await wait(600)
        await page.screenshot({ path: `${OUT_DIR}/profile.png` })
        await page.close()
        console.log('[✓] profile.png')
      }

      // ── Target jobs ────────────────────────────────────────────────────────
      {
        const page = await ctx.newPage()
        await page.goto(`${FRONTEND_URL}/jobs`, { waitUntil: 'networkidle' })
        await wait(800)
        // Open first job file if any
        const firstJob = page.locator('button').filter({ hasText: '.md' }).first()
        if (await firstJob.isVisible().catch(() => false)) {
          await firstJob.click()
          await wait(600)
        }
        await page.screenshot({ path: `${OUT_DIR}/jobs.png` })
        await page.close()
        console.log('[✓] jobs.png')
      }

      // ── Generated CVs (Output page) ────────────────────────────────────────
      {
        const page = await ctx.newPage()
        await page.goto(`${FRONTEND_URL}/output`, { waitUntil: 'networkidle' })
        await wait(800)
        // Click first PDF in list if present
        const firstPdf = page.locator('button').filter({ hasText: '.pdf' }).first()
        if (await firstPdf.isVisible().catch(() => false)) {
          await firstPdf.click()
          await wait(1000)
        }
        await page.screenshot({ path: `${OUT_DIR}/output.png` })
        await page.close()
        console.log('[✓] output.png')
      }

      // ── Gen Config ─────────────────────────────────────────────────────────
      {
        const page = await ctx.newPage()
        await page.goto(`${FRONTEND_URL}/build`, { waitUntil: 'networkidle' })
        await wait(600)
        await page.screenshot({ path: `${OUT_DIR}/config.png` })
        await page.close()
        console.log('[✓] config.png')
      }

      await browser.close()

    } finally {
      backend.kill()
      await wait(500)
    }

  } finally {
    rmSync(tmpRoot, { recursive: true, force: true })
    console.log('[i] Cleaned up temp dir — no personal data was used')
  }

  console.log(`\n[✓] Screenshots saved to ${OUT_DIR}/`)
  console.log('    git add docs/screenshots/ && git commit -m "docs: add app screenshots"')
}

main().catch(e => { console.error(e); process.exit(1) })
