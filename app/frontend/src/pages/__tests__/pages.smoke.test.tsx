/**
 * Smoke tests: verify each page module can be imported without errors.
 *
 * These tests exist to catch TypeScript/JSX syntax errors and broken imports
 * in page components before they reach the browser. A parse error in any
 * page file causes the dynamic import() to reject, failing the test
 * immediately with a clear message pointing to the broken file.
 *
 * No rendering is needed — just importing is enough to trigger compilation.
 */

import { describe, it, expect } from 'vitest'

describe('page modules - syntax smoke tests', () => {
  it('OutputPage loads', async () => {
    const { OutputPage } = await import('../OutputPage')
    expect(OutputPage).toBeDefined()
  })

  it('Dashboard loads', async () => {
    const { Dashboard } = await import('../Dashboard')
    expect(Dashboard).toBeDefined()
  })

  it('BuildPage loads', async () => {
    const { BuildPage } = await import('../BuildPage')
    expect(BuildPage).toBeDefined()
  })

  it('DataBrowser loads', async () => {
    const { DataBrowser } = await import('../DataBrowser')
    expect(DataBrowser).toBeDefined()
  })

  it('JobsPage loads', async () => {
    const { JobsPage } = await import('../JobsPage')
    expect(JobsPage).toBeDefined()
  })
})
