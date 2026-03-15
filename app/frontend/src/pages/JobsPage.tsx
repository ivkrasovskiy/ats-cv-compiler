import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listJobFiles, getJobFile, putJobFile, deleteJobFile } from '../api/client'

export function JobsPage() {
  const qc = useQueryClient()
  const [editing, setEditing] = useState<string | null>(null)
  const [draft, setDraft] = useState('')
  const [newName, setNewName] = useState('')
  const [creating, setCreating] = useState(false)

  const listQ = useQuery({ queryKey: ['files', 'jobs'], queryFn: listJobFiles })

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
    onSuccess: () => void qc.invalidateQueries({ queryKey: ['files', 'jobs'] }),
  })

  const startEdit = (name: string) => {
    setEditing(name)
    setDraft('')
    setCreating(false)
  }

  const startCreate = () => {
    setCreating(true)
    setEditing(null)
    setDraft('')
    setNewName('')
  }

  if (editing && editQ.data && draft === '' && editQ.data.content) {
    setDraft(editQ.data.content)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-100">Job Descriptions</h1>
          <p className="mt-1 text-sm text-slate-400">Manage target job files for tailored CVs</p>
        </div>
        <button
          onClick={startCreate}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
        >
          + New Job
        </button>
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

      {/* File list */}
      {listQ.isLoading && <p className="text-sm text-slate-500">Loading…</p>}
      {listQ.data?.length === 0 && !creating && (
        <p className="text-sm text-slate-500">No job files yet. Click "+ New Job" to create one.</p>
      )}
      {listQ.data && listQ.data.length > 0 && (
        <div className="space-y-2">
          {listQ.data.map(f => (
            <div
              key={f.path}
              className="flex items-center justify-between rounded-lg border border-slate-700 bg-slate-900 px-4 py-3"
            >
              <span className="font-mono text-sm text-slate-300">{f.name}</span>
              <div className="flex gap-2">
                <button
                  onClick={() => startEdit(f.name)}
                  className="rounded bg-slate-700 px-3 py-1 text-xs text-slate-200 hover:bg-slate-600"
                >
                  Edit
                </button>
                <button
                  onClick={() => deleteMut.mutate(f.name)}
                  className="rounded bg-red-900 px-3 py-1 text-xs text-red-200 hover:bg-red-800"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
