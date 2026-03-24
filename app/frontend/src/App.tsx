import { useState } from 'react'
import { BrowserRouter, NavLink, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Dashboard } from './pages/Dashboard'
import { DataBrowser } from './pages/DataBrowser'
import { JobsPage } from './pages/JobsPage'
import { BuildPage } from './pages/BuildPage'
import { OutputPage } from './pages/OutputPage'
import { AgentPage } from './pages/AgentPage'
import { ErrorBoundary } from './ErrorBoundary'
import { RepairNotification } from './components/RepairNotification'

const qc = new QueryClient()

const NAV = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/data', label: 'Profile', end: false },
  { to: '/jobs', label: 'Target Jobs', end: false },
  { to: '/output', label: 'Generated CVs', end: false },
  { to: '/build', label: 'Gen Config', end: false },
  { to: '/agent', label: 'Agent', end: false },
]

type AppAction = 'shutdown' | 'restart' | null

function SystemControls() {
  const [pending, setPending] = useState<AppAction>(null)
  const [done, setDone] = useState<string | null>(null)

  const doAction = async (action: AppAction) => {
    if (!action) return
    setPending(action)
    try {
      await fetch(`/api/system/${action}`, { method: 'POST' })
      if (action === 'shutdown') {
        setDone('App is shutting down. You can close this tab.')
      } else {
        setDone('Restarting… page will reload shortly.')
        // Poll health until backend comes back, then reload
        let attempts = 0
        const id = setInterval(async () => {
          attempts++
          try {
            const res = await fetch('/api/health')
            if (res.ok) {
              clearInterval(id)
              window.location.reload()
            }
          } catch { /* backend restarting */ }
          if (attempts > 30) clearInterval(id)
        }, 1000)
      }
    } catch {
      setPending(null)
    }
  }

  if (done) {
    return <span className="text-xs text-slate-400">{done}</span>
  }

  return (
    <div className="flex items-center gap-1">
      <button
        onClick={() => doAction('restart')}
        disabled={!!pending}
        title="Restart backend"
        className="rounded px-2 py-1 text-xs text-slate-500 hover:bg-slate-800 hover:text-slate-300 disabled:opacity-40"
      >
        {pending === 'restart' ? '⟳…' : '⟳ Restart'}
      </button>
      <button
        onClick={() => doAction('shutdown')}
        disabled={!!pending}
        title="Shut down the app"
        className="rounded px-2 py-1 text-xs text-slate-500 hover:bg-red-950 hover:text-red-300 disabled:opacity-40"
      >
        {pending === 'shutdown' ? '…' : '⏻ Shutdown'}
      </button>
    </div>
  )
}

function Nav() {
  return (
    <nav className="flex h-full items-center gap-1">
      {NAV.map(({ to, label, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          className={({ isActive }) =>
            `rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              isActive ? 'bg-indigo-900 text-indigo-200' : 'text-slate-400 hover:text-slate-200'
            }`
          }
        >
          {label}
        </NavLink>
      ))}
    </nav>
  )
}

export default function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={qc}>
        <BrowserRouter>
          <div className="flex min-h-screen flex-col">
            {/* Header */}
            <header className="sticky top-0 z-10 border-b border-slate-800 bg-slate-950/90 backdrop-blur">
              <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
                <span className="font-mono text-sm font-semibold text-indigo-400">
                  ats-cv-compiler
                </span>
                <Nav />
                <SystemControls />
              </div>
            </header>

            {/* Main */}
            <main className="mx-auto w-full max-w-6xl flex-1 px-6 py-8">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/data" element={<DataBrowser />} />
                <Route path="/jobs" element={<JobsPage />} />
                <Route path="/build" element={<BuildPage />} />
                <Route path="/output" element={<OutputPage />} />
                <Route path="/agent" element={<AgentPage />} />
              </Routes>
            </main>
          </div>

          {/* Global repair notifications (outside routes) */}
          <RepairNotification />
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  )
}
