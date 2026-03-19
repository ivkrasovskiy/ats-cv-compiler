import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  listJobFiles,
  getJobFile,
  putJobFile,
  deleteJobFile,
  listOutFiles,
  startBuild,
  buildStreamUrl,
} from '../api/client'
import type { FileItem } from '../api/client'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { Tooltip } from '../components/Tooltip'

type BuildState = { lines: string[]; status: 'idle' | 'running' | 'done' | 'error' }

function useRowBuild() {
  const [builds, setBuilds] = useState<Record<string, BuildState>>({})

  const run = async (key: string, jobId: string) => {
    setBuilds(prev => ({ ...prev, [key]: { lines: [], status: 'running' } }))
    const src = new EventSource(buildStreamUrl(jobId))
    src.onmessage = (e) => {
      if (e.data === '[DONE]') {
        src.close()
        setBuilds(prev => ({ ...prev, [key]: { ...prev[key], status: 'done' } }))
      } else {
        setBuilds(prev => ({
          ...prev,
          [key]: { ...prev[key], lines: [...(prev[key]?.lines ?? []), e.data] },
        }))
      }
    }
    src.onerror = () => {
      src.close()
      setBuilds(prev => ({ ...prev, [key]: { ...prev[key], status: 'error' } }))
    }
  }

  return { builds, run }
}

export function JobsPage() {
  const qc = useQueryClient()
  const [editing, setEditing] = useState<string | null>(null)
  const [draft, setDraft] = useState('')
  const [newName, setNewName] = useState('')
  const [creating, setCreating] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null)

  const listQ = useQuery({ queryKey: ['files', 'jobs'], queryFn: listJobFiles })
  const outQ = useQuery({ queryKey: ['out'], queryFn: listOutFiles })
  const { builds, run } = useRowBuild()

  const editQ = useQuery({
    queryKey: ['file', 'jobs', editing],
    queryFn: () => getJobFile(editing!),
    enabled: editing !== null,
    staleTime: Infinity,
  })

  const saveMut = useMutation({
    mutationFn: ({ name, content }: { name: string; content: string }) =>
      putJobFile(name, content),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['files', 'jobs'] })
      setEditing(null)
      setCreating(false)
      setNewName('')
      setDraft('')
    },
  })

  const deleteMut = useMutation({
    mutationFn: (name: string) => deleteJobFile(name),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['files', 'jobs'] })
      setDeleteTarget(null)
    },
  })

  if (editing && editQ.data && draft === '' && editQ.data.content) {
    setDraft(editQ.data.content)
  }

  const outNames = new Set((outQ.data ?? []).map((f: FileItem) => f.name))

  const hasCv = (jobName: string) => {
    const base = jobName.replace(/\.md$/, '')
    return outNames.has(`cv_job_${base}.pdf`)
  }

  const handleGenerate = async (jobName: string) => {
    try {
      const { job_id } = await startBuild({ job: `jobs/${jobName}`, llm: 'none' })
      await run(jobName, job_id)
      void qc.invalidateQueries({ queryKey: ['out'] })
    } catch { /* ignore */ }
  }

  const handleGenerateAll = async () => {
    for (const f of listQ.data ?? []) {
      await handleGenerate(f.name)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-100">Target Jobs</h1>
          <p className="mt-1 text-sm text-slate-400">
            Add one description per job you're applying to. One job = one tailored CV.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => void handleGenerateAll()}
            disabled={!listQ.data?.length}
            className="rounded-lg bg-slate-700 px-4 py-2 text-sm font-medium text-slate-200 hover:bg-slate-600 disabled:opacity-50"
          >
            Generate for All
          </button>
          <button
            onClick={() => { setCreating(true); setEditing(null); setDraft(''); setNewName('') }}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
          >
            + New Job
          </button>
        </div>
      </div>

      {/* Create form */}
      {creating && (
        <div className="rounded-xl border border-slate-700 bg-slate-900 p-5 space-y-3">
          <h2 className="text-sm font-medium text-slate-300">New Job Description</h2>
          <input
            value={newName}
            onChange={e => setNewName(e.target.value)}
            placeholder="filename.md (e.g. google_swe.md)"
            className="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-slate-200 placeholder-slate-500 outline-none focus:border-indigo-500"
          />
          <textarea
            value={draft}
            onChange={e => setDraft(e.target.value)}
            placeholder="Paste the job description here…"
            rows={10}
            className="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 font-mono text-sm text-slate-200 placeholder-slate-500 outline-none focus:border-indigo-500"
          />
          <div className="flex gap-2">
            <button
              onClick={() => saveMut.mutate({ name: newName, content: draft })}
              disabled={!newName || saveMut.isPending}
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
            >
              Save
            </button>
            <button
              onClick={() => setCreating(false)}
              className="rounded-lg bg-slate-700 px-4 py-2 text-sm font-medium text-slate-200 hover:bg-slate-600"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Edit form */}
      {editing && editQ.data && (
        <div className="rounded-xl border border-slate-700 bg-slate-900 p-5 space-y-3">
          <h2 className="font-mono text-sm text-slate-300">{editing}</h2>
          <textarea
            value={draft || editQ.data.content}
            onChange={e => setDraft(e.target.value)}
            rows={10}
            className="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 font-mono text-sm text-slate-200 outline-none focus:border-indigo-500"
          />
          <div className="flex gap-2">
            <button
              onClick={() => saveMut.mutate({ name: editing, content: draft })}
              disabled={saveMut.isPending}
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
            >
              Save
            </button>
            <button
              onClick={() => setEditing(null)}
              className="rounded-lg bg-slate-700 px-4 py-2 text-sm font-medium text-slate-200 hover:bg-slate-600"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Job list */}
      {listQ.isLoading && <p className="text-sm text-slate-500">Loading…</p>}
      {listQ.data?.length === 0 && !creating && (
        <p className="text-sm text-slate-500">No job files yet. Click "+ New Job" to create one.</p>
      )}
      {listQ.data && listQ.data.length > 0 && (
        <div className="space-y-3">
          {listQ.data.map(f => {
            const b = builds[f.name] ?? { lines: [], status: 'idle' }
            return (
              <div
                key={f.path}
                className="rounded-xl border border-slate-700 bg-slate-900 p-4"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-slate-400">📄</span>
                    <span className="font-mono text-sm text-slate-300">{f.name}</span>
                    {hasCv(f.name) && (
                      <span className="text-xs text-green-400">✓ CV generated</span>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => { setEditing(f.name); setDraft('') }}
                      className="rounded bg-slate-700 px-3 py-1 text-xs text-slate-200 hover:bg-slate-600"
                    >
                      Edit
                    </button>
                    <Tooltip text="Runs the full CV pipeline for this job description">
                      <button
                        onClick={() => void handleGenerate(f.name)}
                        disabled={b.status === 'running'}
                        className="rounded bg-indigo-700 px-3 py-1 text-xs text-indigo-100 hover:bg-indigo-600 disabled:opacity-50"
                      >
                        {b.status === 'running' ? '…' : '⚡ Generate CV'}
                      </button>
                    </Tooltip>
                    <button
                      onClick={() => setDeleteTarget(f.name)}
                      className="rounded bg-red-900 px-3 py-1 text-xs text-red-200 hover:bg-red-800"
                    >
                      Delete
                    </button>
                  </div>
                </div>
                {b.status !== 'idle' && (
                  <div className="mt-3 max-h-32 overflow-y-auto rounded bg-slate-950 p-2 font-mono text-xs text-slate-300">
                    {b.lines.map((l, i) => <div key={i}>{l}</div>)}
                    {b.status === 'running' && <div className="animate-pulse text-indigo-400">▌</div>}
                    {b.status === 'done' && <div className="text-green-400">✓ Done</div>}
                    {b.status === 'error' && <div className="text-red-400">✗ Error</div>}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {deleteTarget && (
        <ConfirmDialog
          title="Delete job file?"
          message={`Are you sure you want to delete "${deleteTarget}"?`}
          confirmLabel="Delete"
          onConfirm={() => deleteMut.mutate(deleteTarget)}
          onCancel={() => setDeleteTarget(null)}
        />
      )}
    </div>
  )
}
