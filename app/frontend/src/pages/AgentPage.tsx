import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getConfig } from '../api/client'
import { useAgentTerminal } from '../hooks/useAgentTerminal'
import '@xterm/xterm/css/xterm.css'

const CLI_OPTIONS = [
  { value: 'claude', label: 'Claude CLI' },
  { value: 'gemini', label: 'Gemini CLI' },
]

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  idle: { label: 'Not started', color: 'text-slate-500' },
  connecting: { label: 'Connecting…', color: 'text-yellow-400' },
  connected: { label: 'Connected', color: 'text-green-400' },
  disconnected: { label: 'Disconnected', color: 'text-slate-400' },
  error: { label: 'Error', color: 'text-red-400' },
}

export function AgentPage() {
  const configQ = useQuery({ queryKey: ['config'], queryFn: getConfig })
  const defaultCli =
    (configQ.data?.basic['CV_AI_PROVIDER'] === 'gemini' ? 'gemini' : 'claude')
  const [selectedCli, setSelectedCli] = useState<string>(defaultCli)
  const { termRef, status, start, stop } = useAgentTerminal()

  const isRunning = status === 'connected' || status === 'connecting'
  const statusInfo = STATUS_LABELS[status] ?? STATUS_LABELS.idle

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold text-slate-100">Agent Terminal</h1>
        <p className="mt-1 text-sm text-slate-400">
          Talk to your AI CLI directly from the browser — edit CV data, debug issues, ask questions.
        </p>
      </div>

      {/* Toolbar */}
      <div className="flex items-center gap-3 rounded-xl border border-slate-700 bg-slate-900 px-4 py-3">
        <select
          value={selectedCli}
          onChange={e => setSelectedCli(e.target.value)}
          disabled={isRunning}
          className="rounded-lg border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 outline-none focus:border-indigo-500 disabled:opacity-50"
        >
          {CLI_OPTIONS.map(opt => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>

        {!isRunning ? (
          <button
            onClick={() => start(selectedCli)}
            className="rounded-lg bg-indigo-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-indigo-500"
          >
            Start
          </button>
        ) : (
          <button
            onClick={stop}
            className="rounded-lg bg-slate-700 px-4 py-1.5 text-sm font-medium text-slate-200 hover:bg-slate-600"
          >
            Stop
          </button>
        )}

        <span className={`ml-auto text-xs font-medium ${statusInfo.color}`}>
          {statusInfo.label}
        </span>
      </div>

      {/* Terminal container */}
      <div
        className="overflow-hidden rounded-xl border border-slate-700 bg-[#0f172a]"
        style={{ height: '500px', padding: '8px' }}
      >
        <div ref={termRef} style={{ height: '100%', width: '100%' }} />
        {status === 'idle' && (
          <div className="flex h-full items-center justify-center">
            <p className="text-sm text-slate-500">Select a CLI and click Start to begin.</p>
          </div>
        )}
        {status === 'error' && (
          <div className="flex h-full items-center justify-center">
            <p className="text-sm text-red-400">
              Could not connect. Make sure the backend is running and the CLI is installed.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
