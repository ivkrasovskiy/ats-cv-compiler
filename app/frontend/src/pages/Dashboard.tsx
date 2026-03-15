import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { getDoctor, getLint } from '../api/client'
import { StatusCard } from '../components/StatusCard'

export function Dashboard() {
  const navigate = useNavigate()
  const doctor = useQuery({ queryKey: ['doctor'], queryFn: getDoctor })
  const lint = useQuery({ queryKey: ['lint'], queryFn: getLint })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-100">Dashboard</h1>
        <p className="mt-1 text-sm text-slate-400">System status and quick actions</p>
      </div>

      {/* System Status */}
      <section className="rounded-xl border border-slate-700 bg-slate-900 p-5">
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-slate-400">
          System Status
        </h2>
        {doctor.isLoading && <p className="text-sm text-slate-500">Checking…</p>}
        {doctor.isError && (
          <p className="text-sm text-red-400">Could not reach backend. Is the server running?</p>
        )}
        {doctor.data && (
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            {doctor.data.checks.map((c, i) => (
              <StatusCard key={i} check={c} />
            ))}
          </div>
        )}
      </section>

      {/* Quick Actions */}
      <section className="rounded-xl border border-slate-700 bg-slate-900 p-5">
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-slate-400">
          Quick Actions
        </h2>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => navigate('/build')}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
          >
            Build Generic CV
          </button>
          <button
            onClick={() => navigate('/build')}
            className="rounded-lg bg-slate-700 px-4 py-2 text-sm font-medium text-slate-200 hover:bg-slate-600"
          >
            Build for Job ▾
          </button>
          <button
            onClick={() => lint.refetch()}
            className="rounded-lg bg-slate-700 px-4 py-2 text-sm font-medium text-slate-200 hover:bg-slate-600"
          >
            Run Lint
          </button>
          <button
            onClick={() => doctor.refetch()}
            className="rounded-lg bg-slate-700 px-4 py-2 text-sm font-medium text-slate-200 hover:bg-slate-600"
          >
            Run Doctor
          </button>
        </div>
      </section>

      {/* Lint results */}
      {lint.data && (
        <section className="rounded-xl border border-slate-700 bg-slate-900 p-5">
          <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-slate-400">
            Lint Results
          </h2>
          {lint.data.ok ? (
            <p className="text-sm text-green-400">✓ No issues found.</p>
          ) : (
            <ul className="space-y-1">
              {lint.data.issues.map((issue, i) => (
                <li key={i} className="flex gap-2 text-sm">
                  <span
                    className={`shrink-0 font-mono text-xs ${
                      issue.severity === 'ERROR' ? 'text-red-400' : 'text-yellow-400'
                    }`}
                  >
                    {issue.severity}
                  </span>
                  <span className="text-slate-300">{issue.message}</span>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </div>
  )
}
