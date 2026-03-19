import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listDataFiles, getDataFile, putDataFile, deleteDataFile } from '../api/client'
import type { FileItem } from '../api/client'
import { FileEditor } from '../components/FileEditor'
import { ConfirmDialog } from '../components/ConfirmDialog'

const PROFILE_FILES = ['profile.md', 'skills.md', 'education.md', 'experience_summary.md']

function stripPrefix(name: string): string {
  return name
    .replace(/^llm_exp_/, '')
    .replace(/^user_exp_/, '')
    .replace(/^proj_/, '')
    .replace(/\.md$/, '')
}

function Section({
  title,
  files,
  selected,
  onSelect,
  onDelete,
  onAdd,
  canDelete,
  defaultOpen = true,
  tip,
}: {
  title: string
  files: FileItem[]
  selected: string | null
  onSelect: (path: string) => void
  onDelete?: (path: string) => void
  onAdd?: () => void
  canDelete?: boolean
  defaultOpen?: boolean
  tip?: string
}) {
  return (
    <details open={defaultOpen} className="group">
      <summary className="flex cursor-pointer items-center justify-between px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-400 hover:text-slate-300 select-none">
        <span className="flex items-center gap-1">
          <span className="mr-1 text-slate-500 group-open:hidden">▶</span>
          <span className="mr-1 text-slate-500 hidden group-open:inline">▼</span>
          <span>{title}</span>
          {tip && (
            <span
              className="ml-1 cursor-help text-slate-600 hover:text-slate-400"
              title={tip}
              onClick={e => e.preventDefault()}
            >
              ℹ
            </span>
          )}
        </span>
        {onAdd && (
          <button
            onClick={e => { e.preventDefault(); onAdd() }}
            className="rounded bg-slate-700 px-2 py-0.5 text-xs font-medium text-slate-300 hover:bg-slate-600"
          >
            + Add
          </button>
        )}
      </summary>
      <ul className="py-1">
        {files.map(f => (
          <li
            key={f.path}
            className={`group/item flex items-center gap-1 px-3 py-1.5 text-sm ${
              selected === f.path ? 'bg-indigo-900/40 text-indigo-300' : 'text-slate-300 hover:bg-slate-800'
            }`}
          >
            <button
              className="flex-1 truncate text-left"
              onClick={() => onSelect(f.path)}
              title={f.name}
            >
              {stripPrefix(f.name)}
            </button>
            {canDelete && onDelete && (
              <button
                onClick={() => onDelete(f.path)}
                className="shrink-0 rounded px-1 text-xs text-slate-500 opacity-0 hover:text-red-400 group-hover/item:opacity-100"
              >
                ×
              </button>
            )}
          </li>
        ))}
        {files.length === 0 && (
          <li className="px-3 py-1 text-xs text-slate-600">No files</li>
        )}
      </ul>
    </details>
  )
}

export function DataBrowser() {
  const qc = useQueryClient()
  const [selected, setSelected] = useState<string | null>(null)
  const [draft, setDraft] = useState<string>('')
  const [saved, setSaved] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null)
  const [addingIn, setAddingIn] = useState<string | null>(null) // 'experience' | 'projects'
  const [newName, setNewName] = useState('')
  const [confirmDiscard, setConfirmDiscard] = useState(false)

  const treeQ = useQuery({ queryKey: ['files', 'data'], queryFn: listDataFiles })

  const fileQ = useQuery({
    queryKey: ['file', 'data', selected],
    queryFn: () => getDataFile(selected!),
    enabled: selected !== null,
    staleTime: Infinity,
  })

  const saveMut = useMutation({
    mutationFn: () => putDataFile(selected!, draft),
    onSuccess: () => {
      setSaved(true)
      void qc.invalidateQueries({ queryKey: ['files', 'data'] })
      setTimeout(() => setSaved(false), 2000)
    },
  })

  const deleteMut = useMutation({
    mutationFn: (path: string) => deleteDataFile(path),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['files', 'data'] })
      setDeleteTarget(null)
      if (selected === deleteTarget) {
        setSelected(null)
        setDraft('')
      }
    },
  })

  const createMut = useMutation({
    mutationFn: ({ path }: { path: string }) => putDataFile(path, ''),
    onSuccess: (_, { path }) => {
      void qc.invalidateQueries({ queryKey: ['files', 'data'] })
      setAddingIn(null)
      setNewName('')
      handleSelect(path)
    },
  })

  const handleSelect = (path: string) => {
    setSelected(path)
    setDraft('')
    setSaved(false)
  }

  if (fileQ.data && draft === '' && fileQ.data.content) {
    setDraft(fileQ.data.content)
  }

  const files = treeQ.data ?? []

  const profileFiles = files.filter(f => PROFILE_FILES.includes(f.path))
  const experienceFiles = files.filter(f => f.path.startsWith('experience/'))
  const projectFiles = files.filter(f => f.path.startsWith('projects/'))
  const otherFiles = files.filter(
    f =>
      !PROFILE_FILES.includes(f.path) &&
      !f.path.startsWith('experience/') &&
      !f.path.startsWith('projects/'),
  )

  const handleAdd = (dir: string) => {
    setAddingIn(dir)
    setNewName('')
  }

  const handleCreateConfirm = () => {
    if (!newName || !addingIn) return
    const safeName = newName.endsWith('.md') ? newName : `${newName}.md`
    createMut.mutate({ path: `${addingIn}/${safeName}` })
  }

  const handleCancelEdit = () => {
    if (draft !== '') {
      setConfirmDiscard(true)
    } else {
      setSelected(null)
      setDraft('')
    }
  }

  // Skills contextual tip
  const skillCount = selected === 'skills.md'
    ? (draft.match(/^\s+-\s+\S/gm) ?? []).length
    : 0

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-0 overflow-hidden rounded-xl border border-slate-700">
      {/* Left panel */}
      <div className="w-60 shrink-0 overflow-y-auto border-r border-slate-700 bg-slate-900">
        {/* Sticky header + banner */}
        <div className="sticky top-0 z-10 bg-slate-900">
          <div className="border-b border-slate-700 px-3 py-2 text-xs font-medium uppercase tracking-wide text-slate-400">
            Profile Data
          </div>
          <div className="border-b border-indigo-800 bg-indigo-950/40 px-3 py-3 text-xs text-indigo-200">
            <p className="font-medium">These files power every CV you generate.</p>
            <p className="mt-1 text-indigo-300/70">Review and edit them carefully.</p>
            <p className="mt-2 text-indigo-400/80">
              💡 New here?{' '}
              <Link to="/" className="underline text-indigo-300">
                Upload your CV on the Dashboard
              </Link>{' '}
              first.
            </p>
          </div>
        </div>

        {treeQ.isLoading && <p className="px-3 py-2 text-xs text-slate-500">Loading…</p>}

        {/* Add new file inline form */}
        {addingIn && (
          <div className="border-b border-slate-700 px-3 py-2 space-y-2">
            <p className="text-xs text-slate-400">New file in {addingIn}/</p>
            <input
              autoFocus
              value={newName}
              onChange={e => setNewName(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') handleCreateConfirm() }}
              placeholder="filename.md"
              className="w-full rounded border border-slate-600 bg-slate-800 px-2 py-1 text-xs text-slate-200 outline-none focus:border-indigo-500"
            />
            <div className="flex gap-1">
              <button
                onClick={handleCreateConfirm}
                disabled={!newName || createMut.isPending}
                className="rounded bg-indigo-600 px-2 py-1 text-xs text-white disabled:opacity-50"
              >
                Create
              </button>
              <button
                onClick={() => setAddingIn(null)}
                className="rounded bg-slate-700 px-2 py-1 text-xs text-slate-300"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Sections: Profile → Projects → Experience → Other */}
        <Section
          title="Profile"
          files={profileFiles}
          selected={selected}
          onSelect={handleSelect}
          canDelete={false}
          tip="Fill in all fields — especially about_me (2-3 sentences) and links (LinkedIn, GitHub)."
        />
        <Section
          title="Projects"
          files={projectFiles}
          selected={selected}
          onSelect={handleSelect}
          onDelete={setDeleteTarget}
          onAdd={() => handleAdd('projects')}
          canDelete={true}
          tip="One file per project or initiative. More projects = better job targeting."
        />
        <Section
          title="Experience"
          files={experienceFiles}
          selected={selected}
          onSelect={handleSelect}
          onDelete={setDeleteTarget}
          onAdd={() => handleAdd('experience')}
          canDelete={true}
          tip="One file per employer. Bullets describe outcomes — the AI pipeline rewrites these."
        />
        <Section
          title="Other"
          files={otherFiles}
          selected={selected}
          onSelect={handleSelect}
          canDelete={false}
          defaultOpen={false}
        />
      </div>

      {/* Right panel */}
      <div className="flex-1 overflow-hidden bg-slate-950">
        {!selected && (
          <div className="flex h-full items-center justify-center text-lg font-medium text-slate-100">
            Select a file to edit.
          </div>
        )}
        {selected && fileQ.isLoading && (
          <div className="flex h-full items-center justify-center text-sm text-slate-500">
            Loading…
          </div>
        )}
        {selected && fileQ.data && (
          <div className="flex h-full flex-col overflow-hidden">
            {/* Skills contextual tip */}
            {selected === 'skills.md' && (
              <div className="border-b border-yellow-800 bg-yellow-950/30 px-4 py-2 text-xs text-yellow-300 shrink-0">
                Add as many skills as possible — the system picks the most relevant ones per target job. Aim for 20+ skills.
                {skillCount < 10 && (
                  <span className="ml-1 font-semibold text-yellow-200">
                    ⚠️ You have fewer than 10 skills — add more for better results.
                  </span>
                )}
              </div>
            )}
            <div className="flex-1 overflow-hidden">
              <FileEditor
                path={selected}
                content={draft || fileQ.data.content}
                onChange={v => {
                  setDraft(v)
                  setSaved(false)
                }}
                onSave={() => saveMut.mutate()}
                onCancel={handleCancelEdit}
                saving={saveMut.isPending}
                saved={saved}
                lang="yaml"
              />
            </div>
          </div>
        )}
      </div>

      {/* Confirm delete dialog */}
      {deleteTarget && (
        <ConfirmDialog
          title="Delete file?"
          message={`Are you sure you want to delete "${deleteTarget}"? This cannot be undone.`}
          confirmLabel="Delete"
          onConfirm={() => deleteMut.mutate(deleteTarget)}
          onCancel={() => setDeleteTarget(null)}
        />
      )}

      {/* Confirm discard changes */}
      {confirmDiscard && (
        <ConfirmDialog
          title="Discard changes?"
          message="Your unsaved changes will be lost."
          confirmLabel="Discard"
          cancelLabel="Keep editing"
          onConfirm={() => {
            setConfirmDiscard(false)
            setSelected(null)
            setDraft('')
          }}
          onCancel={() => setConfirmDiscard(false)}
        />
      )}
    </div>
  )
}
