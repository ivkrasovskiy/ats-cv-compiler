import { useEffect, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

interface RepairEvent {
  id: string
  ts: string
  error_entry: {
    status: number
    method: string
    path: string
    traceback: string | null
    error: string | null
  }
  error_type: string
  reason: string
  fix_hint: string
  status: string
  fix_output: string
  gh_issue_url: string
}

interface SSEEvent {
  type: 'logic_error' | 'fixing' | 'fix_applied' | string
  event: RepairEvent
}

type RepairMode = 'silent' | 'approval' | 'inform'

async function fetchRepairStatus() {
  const res = await fetch('/api/repair/status')
  return res.json() as Promise<{ event: RepairEvent | null; gh_available: boolean }>
}

export function RepairNotification() {
  const [toast, setToast] = useState<SSEEvent | null>(null)
  const [expanded, setExpanded] = useState(false)
  const esRef = useRef<EventSource | null>(null)
  const repairMode = useRef<RepairMode>('silent')

  const statusQ = useQuery({
    queryKey: ['repair-status'],
    queryFn: fetchRepairStatus,
    enabled: !!toast,
    refetchInterval: false,
  })

  // Read repair mode from config on mount
  useEffect(() => {
    fetch('/api/config')
      .then(r => r.json())
      .then(data => {
        const mode = data?.basic?.CV_REPAIR_MODE ?? 'silent'
        repairMode.current = mode as RepairMode
      })
      .catch(() => {})
  }, [])

  useEffect(() => {
    const es = new EventSource('/api/repair/stream')
    esRef.current = es

    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data) as SSEEvent
        setToast(data)

        if (data.type === 'fix_applied') {
          // Poll /api/health then reload
          pollAndReload()
        }
      } catch {
        // heartbeat / parse error — ignore
      }
    }

    return () => {
      es.close()
    }
  }, [])

  function pollAndReload() {
    let attempts = 0
    const id = setInterval(async () => {
      attempts++
      try {
        const res = await fetch('/api/health')
        if (res.ok) {
          clearInterval(id)
          setTimeout(() => window.location.reload(), 500)
        }
      } catch {
        // backend restarting
      }
      if (attempts > 30) clearInterval(id)
    }, 1000)
  }

  async function handleApprove() {
    await fetch('/api/repair/apply', { method: 'POST' })
    setToast(null)
  }

  async function handleDismiss() {
    await fetch('/api/repair/dismiss', { method: 'POST' })
    setToast(null)
  }

  async function handleCreateIssue() {
    if (!toast) return
    const title = `Backend error: ${toast.event.error_entry.method} ${toast.event.error_entry.path} → ${toast.event.error_entry.status}`
    const body = `**Reason:** ${toast.event.reason}\n\n**Traceback:**\n\`\`\`\n${toast.event.error_entry.traceback ?? 'N/A'}\n\`\`\``
    const res = await fetch('/api/repair/github-issue', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, body }),
    })
    const data = await res.json()
    if (data.url) {
      window.open(data.url, '_blank', 'noopener')
    }
  }

  if (!toast) return null

  const mode = repairMode.current
  const isFixApplied = toast.type === 'fix_applied'
  const isFixing = toast.type === 'fixing'

  return (
    <div className="fixed bottom-4 right-4 z-50 w-80 rounded-xl border border-slate-700 bg-slate-900 p-4 shadow-xl text-sm">
      {isFixApplied ? (
        <>
          <div className="flex items-center justify-between">
            <span className="font-medium text-green-400">Auto-repair applied</span>
            <button onClick={() => setToast(null)} className="text-slate-500 hover:text-slate-300">✕</button>
          </div>
          <p className="mt-1 text-xs text-slate-400">Restarting app…</p>
        </>
      ) : isFixing ? (
        <>
          <div className="flex items-center gap-2">
            <span className="font-medium text-yellow-400">Auto-repair in progress…</span>
          </div>
          <p className="mt-1 text-xs text-slate-400">{toast.event.reason}</p>
        </>
      ) : (
        <>
          <div className="flex items-center justify-between">
            <span className="font-medium text-red-400">Backend error detected</span>
            <button onClick={() => setToast(null)} className="text-slate-500 hover:text-slate-300">✕</button>
          </div>

          <p className="mt-1 text-xs text-slate-300">{toast.event.reason}</p>

          {mode === 'silent' && (
            <p className="mt-2 text-xs text-slate-500">Auto-repair queued…</p>
          )}

          {mode === 'approval' && (
            <div className="mt-3 flex gap-2">
              <button
                onClick={handleApprove}
                className="rounded bg-indigo-600 px-3 py-1 text-xs font-medium text-white hover:bg-indigo-500"
              >
                Approve Fix
              </button>
              <button
                onClick={handleDismiss}
                className="rounded bg-slate-700 px-3 py-1 text-xs text-slate-300 hover:bg-slate-600"
              >
                Dismiss
              </button>
              {toast.event.error_entry.traceback && (
                <button
                  onClick={() => setExpanded(x => !x)}
                  className="rounded bg-slate-700 px-3 py-1 text-xs text-slate-300 hover:bg-slate-600"
                >
                  {expanded ? 'Hide' : 'Traceback'}
                </button>
              )}
            </div>
          )}

          {mode === 'inform' && (
            <div className="mt-3 flex gap-2">
              <a
                href="/agent"
                className="rounded bg-indigo-600 px-3 py-1 text-xs font-medium text-white hover:bg-indigo-500"
              >
                Fix with AI →
              </a>
              {toast.event.error_entry.traceback && (
                <button
                  onClick={() => setExpanded(x => !x)}
                  className="rounded bg-slate-700 px-3 py-1 text-xs text-slate-300 hover:bg-slate-600"
                >
                  {expanded ? 'Hide' : 'Traceback'}
                </button>
              )}
            </div>
          )}

          {expanded && toast.event.error_entry.traceback && (
            <pre className="mt-3 max-h-32 overflow-auto rounded bg-slate-800 p-2 text-xs text-slate-400">
              {toast.event.error_entry.traceback}
            </pre>
          )}

          {statusQ.data?.gh_available && (
            <button
              onClick={handleCreateIssue}
              className="mt-2 text-xs text-slate-500 underline hover:text-slate-400"
            >
              Create GitHub Issue
            </button>
          )}
        </>
      )}
    </div>
  )
}
