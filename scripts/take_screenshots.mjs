#!/usr/bin/env node
/**
 * scripts/take_screenshots.mjs
 * Screenshots all 5 app pages using example (Jordan Blake) data only.
 * Personal data is never read.
 *
 * Usage: bash scripts/run_screenshots.sh
 * (Frontend dev server must be running on :5173)
 */

import { chromium } from '../app/e2e/node_modules/playwright/index.mjs'
import { spawn, execSync } from 'child_process'
import { mkdirSync, cpSync, mkdtempSync, rmSync } from 'fs'
import { join } from 'path'
import { tmpdir } from 'os'

const FRONTEND = 'http://localhost:5173'
const BACKEND  = 'http://localhost:8000'
const OUT_DIR  = 'docs/screenshots'

const wait = ms => new Promise(r => setTimeout(r, ms))

async function waitForBackend(maxMs = 20_000) {
  const deadline = Date.now() + maxMs
  while (Date.now() < deadline) {
    try { if ((await fetch(`${BACKEND}/api/health`)).ok) return } catch {}
    await wait(400)
  }
  throw new Error('Backend did not come up in time')
}

async function main() {
  // ── 1. Build clean example project in a temp dir ──────────────────────────
  const root = mkdtempSync(join(tmpdir(), 'ats-demo-'))
  console.log(`[i] Temp root: ${root}`)

  try {
    // Copy example data + jobs only (no user data ever)
    cpSync('examples/basic/data', join(root, 'data'), { recursive: true })
    cpSync('examples/basic/jobs', join(root, 'jobs'), { recursive: true })
    mkdirSync(join(root, 'out'), { recursive: true })

    console.log('[…] Building example CV (Jordan Blake)…')
    const outDir = join(root, 'out')
    try {
      execSync(
        `uv run cv build --data "${join(root, 'data')}" --job false`,
        { stdio: 'pipe' }
      )
      // Move built files to our temp out/
      execSync(`mv out/cv_generic.* "${outDir}/" 2>/dev/null || true`, { shell: true, stdio: 'pipe' })

      execSync(
        `uv run cv build --data "${join(root, 'data')}" --job "${join(root, 'jobs/backend_engineer.md')}"`,
        { stdio: 'pipe' }
      )
      execSync(`mv out/cv_job_*.* "${outDir}/" 2>/dev/null || true`, { shell: true, stdio: 'pipe' })

      console.log('[✓] Build done —', execSync(`ls "${outDir}"`).toString().trim().replace(/\n/g, ', '))
    } catch (e) {
      console.warn('[!] Build failed — output page may be empty\n', e.stderr?.toString().slice(0, 300))
    }

    // ── 2. Start backend (kill any stale process on :8000 first) ─────────────
    // reload=False: uvicorn --reload uses multiprocessing "spawn" on macOS
    // which does NOT inherit env vars → CV_PROJECT_ROOT would be lost.
    try {
      execSync('lsof -ti:8000 | xargs kill -9 2>/dev/null; sleep 0.5', { shell: true, stdio: 'pipe' })
    } catch {}
    console.log('[…] Starting backend…')
    const backend = spawn('uv', [
      'run', '--extra', 'app', 'python', '-c',
      'import uvicorn; uvicorn.run("app.backend.main:app", host="0.0.0.0", port=8000, reload=False)',
    ], {
      env: { ...process.env, CV_PROJECT_ROOT: root },
      stdio: 'pipe',
    })
    backend.on('error', e => { throw e })

    try {
      await waitForBackend()
      console.log('[✓] Backend ready')

      mkdirSync(OUT_DIR, { recursive: true })
      const browser = await chromium.launch()

      // Shared context — dark mode, 1280×800
      const ctx = await browser.newContext({
        viewport: { width: 1280, height: 800 },
        colorScheme: 'dark',
      })

      // ── Screenshot 1: Dashboard — post-parse "done" state ─────────────────
      // We mock /api/ingest/pdf so the UI shows the parse-complete checklist
      // without needing a real LLM call.
      {
        const page = await ctx.newPage()

        // Show Getting Started checklist
        await page.goto(FRONTEND, { waitUntil: 'networkidle' })
        await page.evaluate(() => localStorage.removeItem('ats_onboarded'))

        // Mock the upload + ingest endpoints so the UI reaches "parse done" state
        await page.route('**/api/upload/cv-pdf', route =>
          route.fulfill({ status: 200, contentType: 'application/json',
            body: JSON.stringify({ saved: true, path: 'data/cv.pdf' }) }))

        await page.route('**/api/ingest/pdf', route =>
          route.fulfill({ status: 200, contentType: 'application/json',
            body: JSON.stringify({
              written: [
                'data/profile.md', 'data/skills.md', 'data/education.md',
                'data/projects/proj_backend_platform.md',
                'data/projects/proj_observability.md',
              ],
              warnings: [],
            })
          }))

        await page.reload({ waitUntil: 'networkidle' })
        await wait(400)

        // Simulate: choose a PDF file (triggers uploadDone = true)
        await page.evaluate(() => {
          // Directly set the upload-done state by dispatching a fake successful upload.
          // We trigger the hidden file input's change event with a dummy File.
          const input = document.querySelector('input[type=file]')
          if (!input) return
          const dt = new DataTransfer()
          dt.items.add(new File(['%PDF-1.4'], 'cv.pdf', { type: 'application/pdf' }))
          Object.defineProperty(input, 'files', { value: dt.files })
          input.dispatchEvent(new Event('change', { bubbles: true }))
        })
        await wait(1200)  // wait for upload mock to resolve

        // Now click "Parse with AI →"
        const parseBtn = page.locator('button', { hasText: 'Parse with AI' })
        if (await parseBtn.isVisible().catch(() => false)) {
          await parseBtn.click()
          await wait(800)
        }

        await page.screenshot({ path: `${OUT_DIR}/dashboard.png` })
        await page.close()
        console.log('[✓] dashboard.png')
      }

      // ── Screenshot 2: Profile editor — profile.md open with filled form ───
      {
        const page = await ctx.newPage()
        await page.goto(`${FRONTEND}/data`, { waitUntil: 'networkidle' })
        await wait(600)

        // Click "profile" in the PROFILE section (stripPrefix removes .md)
        const profileBtn = page.locator('button', { hasText: /^profile$/ }).first()
        if (await profileBtn.isVisible().catch(() => false)) {
          await profileBtn.click()
          await wait(900)  // let form load
        }

        await page.screenshot({ path: `${OUT_DIR}/profile.png` })
        await page.close()
        console.log('[✓] profile.png')
      }

      // ── Screenshot 3: Target Jobs — job description open ──────────────────
      {
        const page = await ctx.newPage()
        await page.goto(`${FRONTEND}/jobs`, { waitUntil: 'networkidle' })
        await wait(600)

        // Click first job file button
        const jobBtn = page.locator('button').filter({ hasText: 'backend_engineer' }).first()
        if (await jobBtn.isVisible().catch(() => false)) {
          await jobBtn.click()
          await wait(700)
        } else {
          // fallback: first .md button
          const any = page.locator('button').filter({ hasText: /\.md/ }).first()
          if (await any.isVisible().catch(() => false)) { await any.click(); await wait(700) }
        }

        await page.screenshot({ path: `${OUT_DIR}/jobs.png` })
        await page.close()
        console.log('[✓] jobs.png')
      }

      // ── Screenshot 4: Generated CVs — PDF preview open ───────────────────
      {
        const page = await ctx.newPage()
        await page.goto(`${FRONTEND}/output`, { waitUntil: 'networkidle' })
        await wait(600)

        // Headless Chromium doesn't render PDFs in iframes (plugin disabled).
        // Click "View MD" on the job-targeted CV to show the generated markdown content.
        // The markdown renders fully and makes a great product screenshot.
        const viewMdBtns = page.locator('button', { hasText: 'View MD' })
        const count = await viewMdBtns.count()
        // Second "View MD" belongs to cv_job_backend_engineer (more interesting)
        const viewMdBtn = count >= 2 ? viewMdBtns.nth(1) : viewMdBtns.first()
        if (await viewMdBtn.isVisible().catch(() => false)) {
          await viewMdBtn.click()
          await wait(800)
        }

        await page.screenshot({ path: `${OUT_DIR}/output.png` })
        await page.close()
        console.log('[✓] output.png')
      }

      // ── Screenshot 5: Gen Config ───────────────────────────────────────────
      {
        const page = await ctx.newPage()
        await page.goto(`${FRONTEND}/build`, { waitUntil: 'networkidle' })
        await wait(600)
        await page.screenshot({ path: `${OUT_DIR}/config.png` })
        await page.close()
        console.log('[✓] config.png')
      }

      await browser.close()

    } finally {
      backend.kill()
      await wait(300)
    }

  } finally {
    rmSync(root, { recursive: true, force: true })
    console.log('[i] Temp dir removed — no personal data was used')
  }

  console.log(`\n[✓] Screenshots saved to ${OUT_DIR}/`)
  console.log('    git add docs/screenshots/ && git commit -m "docs: add app screenshots"')
}

main().catch(e => { console.error(e); process.exit(1) })
