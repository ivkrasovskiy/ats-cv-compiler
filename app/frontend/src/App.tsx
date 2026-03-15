import { BrowserRouter, NavLink, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Dashboard } from './pages/Dashboard'
import { DataBrowser } from './pages/DataBrowser'
import { JobsPage } from './pages/JobsPage'
import { BuildPage } from './pages/BuildPage'
import { OutputPage } from './pages/OutputPage'

const qc = new QueryClient()

const NAV = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/data', label: 'Data', end: false },
  { to: '/jobs', label: 'Jobs', end: false },
  { to: '/build', label: 'Build', end: false },
  { to: '/output', label: 'Output', end: false },
]

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
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
