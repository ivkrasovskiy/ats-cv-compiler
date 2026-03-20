import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listDataFiles, getDataFile, putDataFile, deleteDataFile } from '../api/client'
import type { FileItem } from '../api/client'
import { FileEditor } from '../components/FileEditor'
import { BlockEditor } from '../components/BlockEditor'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { ProfileForm } from '../components/form/ProfileForm'
import { SkillsForm } from '../components/form/SkillsForm'
import { EducationForm } from '../components/form/EducationForm'
import { ExperienceForm } from '../components/form/ExperienceForm'
import { ProjectForm } from '../components/form/ProjectForm'

const PROFILE_FILES = ['profile.md', 'skills.md', 'education.md', 'experience_summary.md']

const FORM_SUPPORTED_TYPES = new Set(['profile', 'skills', 'education', 'experience', 'project'])

type EditMode = 'form' | 'blocks' | 'raw'

function inferFileType(path: string): string | null {
  if (path === 'profile.md') return 'profile'
  if (path === 'skills.md') return 'skills'
  if (path === 'education.md') return 'education'
  if (path.startsWith('experience/') && path.endsWith('.md')) return 'experience'
  if (path.startsWith('projects/') && path.endsWith('.md')) return 'project'
  return null
}

function defaultMode(path: string): EditMode {
  const ft = inferFileType(path)
  if (ft !== null && FORM_SUPPORTED_TYPES.has(ft)) return 'form'
  if (path.endsWith('.md')) return 'blocks'
  return 'raw'
}

function FormView({ path, fileType, onSaved }: { path: string; fileType: string; onSaved: () => void }) {
  switch (fileType) {
    case 'profile': return <ProfileForm path={path} onSaved={onSaved} />
    case 'skills': return <SkillsForm path={path} onSaved={onSaved} />
    case 'education': return <EducationForm path={path} onSaved={onSaved} />
    case 'experience': return <ExperienceForm path={path} onSaved={onSaved} />
    case 'project': return <ProjectForm path={path} onSaved={onSaved} />
    default: return null
  }
}

function stripPrefix(name: string): string {
  return name
    .replace(/^llm_exp_/, '')
    .replace(/^user_exp_/, '')
    .replace(/^proj_/, '')
    .replace(/\.md$/, '')
}

function groupByCompany(files: FileItem[]): { company: string; files: FileItem[] }[] {
  const map = new Map<string, FileItem[]>()
  for (const f of files) {
    const key = f.company ?? ''
    if (!map.has(key)) map.set(key, [])
    map.get(key)!.push(f)
  }
  return [...map.entries()]
    .sort(([a], [b]) => {
      if (a === '' && b !== '') return 1
      if (a !== '' && b === '') return -1
      return a.localeCompare(b)
    })
    .map(([company, files]) => ({ company, files }))
}

function FileList({
  files,
  selected,
  onSelect,
  onDelete,
  canDelete,
}: {
  files: FileItem[]
  selected: string | null
  onSelect: (path: string) => void
  onDelete?: (path: string) => void
  canDelete?: boolean
}) {
  return (
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
      {files.length === 0 && <li className="px-3 py-1 text-xs text-slate-600">No files</li>}
    </ul>
  )
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
      <FileList files={files} selected={selected} onSelect={onSelect} onDelete={onDelete} canDelete={canDelete} />
    </details>
  )
}

function GroupedSection({
  title,
  files,
  selected,
  onSelect,
  onDelete,
  onAdd,
  canDelete,
  tip,
}: {
  title: string
  files: FileItem[]
  selected: string | null
  onSelect: (path: string) => void
  onDelete?: (path: string) => void
  onAdd?: () => void
  canDelete?: boolean
  tip?: string
}) {
  const groups = groupByCompany(files)
  const hasCompanies = groups.some(g => g.company !== '')

  return (
    <details open className="group">
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
      {hasCompanies ? (
        groups.map(({ company, files: groupFiles }) => (
          <div key={company || '__none__'}>
            {company && (
              <div className="px-3 pt-2 pb-0.5 text-xs font-medium text-slate-500 uppercase tracking-wide border-t border-slate-800 mt-1">
                {company}
              </div>
            )}
            <FileList
              files={groupFiles}
              selected={selected}
              onSelect={onSelect}
              onDelete={onDelete}
              canDelete={canDelete}
            />
          </div>
        ))
      ) : (
        <FileList files={files} selected={selected} onSelect={onSelect} onDelete={onDelete} canDelete={canDelete} />
      )}
    </details>
  )
}

export function DataBrowser() {
  const qc = useQueryClient()
  const [selected, setSelected] = useState<string | null>(null)
  const [draft, setDraft] = useState<string>('')
  const [saved, setSaved] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null)
  const [addingIn, setAddingIn] = useState<string | null>(null)
  const [newName, setNewName] = useState('')
  const [confirmDiscard, setConfirmDiscard] = useState(false)
  const [editMode, setEditMode] = useState<EditMode>('form')

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
    setEditMode(defaultMode(path))
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

  const skillCount = selected === 'skills.md'
    ? (draft.match(/^\s+-\s+\S/gm) ?? []).length
    : 0

  const fileType = selected ? inferFileType(selected) : null
  const isFormSupported = fileType !== null && FORM_SUPPORTED_TYPES.has(fileType)
  const isMd = selected?.endsWith('.md') ?? false

  const handleFormSaved = () => {
    setSaved(true)
    void qc.invalidateQueries({ queryKey: ['files', 'data'] })
    setTimeout(() => setSaved(false), 2000)
  }

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

        <Section
          title="Profile"
          files={profileFiles}
          selected={selected}
          onSelect={handleSelect}
          canDelete={false}
          tip="Fill in all fields — especially about_me (2-3 sentences) and links (LinkedIn, GitHub)."
        />
        <GroupedSection
          title="Projects"
          files={projectFiles}
          selected={selected}
          onSelect={handleSelect}
          onDelete={setDeleteTarget}
          onAdd={() => handleAdd('projects')}
          canDelete={true}
          tip="One file per project or initiative. More projects = better job targeting."
        />
        <GroupedSection
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
        {selected && fileQ.isLoading && editMode !== 'form' && (
          <div className="flex h-full items-center justify-center text-sm text-slate-500">
            Loading…
          </div>
        )}
        {selected && (editMode === 'form' ? isFormSupported : fileQ.data !== undefined) && (
          <div className="flex h-full flex-col overflow-hidden">
            {/* Top bar: filename + mode toggle */}
            <div className="flex items-center justify-between border-b border-slate-700 px-4 py-2 shrink-0">
              <span className="font-mono text-sm text-slate-400">{selected}</span>
              <div className="flex gap-1">
                {isFormSupported && (
                  <button
                    onClick={() => setEditMode('form')}
                    className={`rounded px-3 py-1 text-xs transition-colors ${
                      editMode === 'form'
                        ? 'bg-indigo-700 text-white'
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    }`}
                    title="Structured form editor"
                  >
                    Form
                  </button>
                )}
                {isMd && (
                  <button
                    onClick={() => setEditMode('blocks')}
                    className={`rounded px-3 py-1 text-xs transition-colors ${
                      editMode === 'blocks'
                        ? 'bg-indigo-700 text-white'
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    }`}
                    title="Split frontmatter + body editors"
                  >
                    Blocks
                  </button>
                )}
                <button
                  onClick={() => setEditMode('raw')}
                  className={`rounded px-3 py-1 text-xs transition-colors ${
                    editMode === 'raw'
                      ? 'bg-indigo-700 text-white'
                      : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                  }`}
                  title="Raw file editor"
                >
                  Raw
                </button>
              </div>
            </div>

            {/* Skills contextual tip */}
            {selected === 'skills.md' && (
              <div className="border-b border-yellow-800 bg-yellow-950/30 px-4 py-2 text-xs text-yellow-300 shrink-0">
                Add as many skills as possible — the system picks the most relevant ones per target job. Aim for 20+ skills.
                {skillCount < 10 && (
                  <span className="ml-1 font-semibold text-yellow-200">
                    ⚠ You have fewer than 10 skills — add more for better results.
                  </span>
                )}
              </div>
            )}

            <div className="flex-1 overflow-y-auto">
              {editMode === 'form' && fileType !== null ? (
                <FormView path={selected} fileType={fileType} onSaved={handleFormSaved} />
              ) : editMode === 'blocks' && isMd && fileQ.data ? (
                <BlockEditor
                  key={selected}
                  content={draft || fileQ.data.content}
                  onChange={v => { setDraft(v); setSaved(false) }}
                  onSave={() => saveMut.mutate()}
                  onCancel={handleCancelEdit}
                  saving={saveMut.isPending}
                  saved={saved}
                />
              ) : fileQ.data ? (
                <FileEditor
                  path={selected}
                  content={draft || fileQ.data.content}
                  onChange={v => { setDraft(v); setSaved(false) }}
                  onSave={() => saveMut.mutate()}
                  onCancel={handleCancelEdit}
                  saving={saveMut.isPending}
                  saved={saved}
                  lang="yaml"
                />
              ) : (
                <div className="flex h-full items-center justify-center text-sm text-slate-500">Loading…</div>
              )}
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
