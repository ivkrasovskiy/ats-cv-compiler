import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  listJobFiles,
  getJobFile,
  putJobFile,
  deleteJobFile,
  listOutFiles,
  startBuild,
} from '../api/client'
import type { FileItem } from '../api/client'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { Tooltip } from '../components/Tooltip'
import { useBuildRun } from '../hooks/useBuildRun'
import { BuildProgress } from '../components/BuildProgress'

export function JobsPage() {
  const qc = useQueryClient()
  const [editing, setEditing] = useState<string | null>(null)
  const [draft, setDraft] = useState('')
  const [newName, setNewName] = useState('')
  const [creating, setCreating] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null)
  const [previewJob, setPreviewJob] = useState<string | null>(null)
  const [expandedJob, setExpandedJob] = useState<string | null>(null)
  const [coverLetterJobs, setCoverLetterJobs] = useState<Set<string>>(new Set())

  const listQ = useQuery({ queryKey: ['files', 'jobs'], queryFn: listJobFiles })
  const outQ = useQuery({ queryKey: ['out'], queryFn: listOutFiles })
  const { builds, run } = useBuildRun()

  const editQ = useQuery({
    queryKey: ['file', 'jobs', editing],
    queryFn: () => getJobFile(editing!),
    enabled: editing !== null,
    staleTime: Infinity,
  })

  const expandQ = useQuery({
    queryKey: ['file', 'jobs', expandedJob],
    queryFn: () => getJobFile(expandedJob!),
    enabled: expandedJob !== null,
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

  // The pipeline names the output cv_<job.id>.pdf where job.id comes from the job
  // file's frontmatter `id` field. If that id starts with "job_" (e.g. job_google)
  // the output is cv_job_google.pdf; otherwise it's cv_<stem>.pdf.
  // So we check both possibilities.
  const cvFileName = (jobName: string): string | null => {
    const base = jobName.replace(/\.md$/, '')
    if (outNames.has(`cv_job_${base}.pdf`)) return `cv_job_${base}.pdf`
    if (outNames.has(`cv_${base}.pdf`)) return `cv_${base}.pdf`
    return null
  }

  const hasCv = (jobName: string) => cvFileName(jobName) !== null

  const handleGenerate = async (jobName: string) => {
    try {
      const { job_id } = await startBuild({
        job: `jobs/${jobName}`,
        llm: 'auto',
        cover_letter: coverLetterJobs.has(jobName),
      })
      await run(jobName, job_id)
      void qc.invalidateQueries({ queryKey: ['out'] })
    } catch { /* ignore */ }
  }

  const visibleJobs = (listQ.data ?? []).filter(f => f.name.toLowerCase() !== 'readme.md')

  const handleGenerateAll = async () => {
    for (const f of visibleJobs) {
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
          <p className="mt-1 text-xs text-slate-500">
            Generated CVs are saved in the{' '}
            <Link to="/output" className="underline text-indigo-400">Generated CVs</Link>
            {' '}tab — open it to edit, re-render, or download.
          </p>
          <p className="mt-2 text-xs text-slate-500">
            Files must use the <code className="rounded bg-slate-800 px-1 text-slate-300">.md</code> extension —{' '}
            <a
              href="https://www.markdownguide.org/basic-syntax/"
              target="_blank"
              rel="noopener noreferrer"
              className="underline text-indigo-400"
            >
              Markdown
            </a>
            {' '}is just plain text with optional formatting like <code className="rounded bg-slate-800 px-1 text-slate-300">**bold**</code> or bullet lists. You can paste a raw job description and it works fine as-is.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => void handleGenerateAll()}
            disabled={!visibleJobs.length}
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
          <div>
            <input
              value={newName}
              onChange={e => setNewName(e.target.value)}
              placeholder="e.g. google_swe.md"
              className={`w-full rounded-lg border px-3 py-2 text-sm text-slate-200 placeholder-slate-500 outline-none bg-slate-800 ${
                newName && !newName.endsWith('.md')
                  ? 'border-red-500 focus:border-red-400'
                  : 'border-slate-600 focus:border-indigo-500'
              }`}
            />
            {newName && !newName.endsWith('.md') && (
              <p className="mt-1 text-xs text-red-400">
                Filename must end in <code className="rounded bg-slate-800 px-1">.md</code> — e.g. <code className="rounded bg-slate-800 px-1">{newName.replace(/\.[^.]*$/, '') || newName}.md</code>
              </p>
            )}
          </div>
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
              disabled={!newName || !newName.endsWith('.md') || saveMut.isPending}
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
      {visibleJobs.length === 0 && !creating && !listQ.isLoading && (
        <p className="text-sm text-slate-500">No job files yet. Click "+ New Job" to create one.</p>
      )}
      {visibleJobs.length > 0 && (
        <div className="space-y-3">
          {visibleJobs.map(f => {
            const b = builds[f.name] ?? { lines: [], status: 'idle' }
            return (
              <div
                key={f.path}
                className="rounded-xl border border-slate-700 bg-slate-900 p-4"
              >
                <div className="flex items-center justify-between">
                  <button
                    className="flex items-center gap-2 text-left hover:text-slate-100"
                    onClick={() => setExpandedJob(expandedJob === f.name ? null : f.name)}
                  >
                    <span className="text-slate-400 text-xs">{expandedJob === f.name ? '▼' : '▶'}</span>
                    <span className="font-mono text-sm text-slate-300">{f.name}</span>
                    {hasCv(f.name) && (
                      <span className="text-xs text-green-400">✓ CV generated</span>
                    )}
                  </button>
                  <div className="flex gap-2">
                    {hasCv(f.name) && (
                      <button
                        onClick={() => setPreviewJob(previewJob === f.name ? null : f.name)}
                        className="rounded bg-slate-700 px-3 py-1 text-xs text-slate-200 hover:bg-slate-600"
                      >
                        {previewJob === f.name ? 'Hide PDF' : 'PDF Preview'}
                      </button>
                    )}
                    {hasCv(f.name) && (
                      <a
                        href={`/api/out/${cvFileName(f.name)}`}
                        download
                        className="rounded bg-slate-700 px-3 py-1 text-xs text-slate-200 hover:bg-slate-600"
                      >
                        ↓ Download
                      </a>
                    )}
                    <button
                      onClick={() => { setEditing(f.name); setDraft(''); setExpandedJob(null) }}
                      className="rounded bg-slate-700 px-3 py-1 text-xs text-slate-200 hover:bg-slate-600"
                    >
                      Edit
                    </button>
                    <label className="flex items-center gap-1 cursor-pointer text-xs text-slate-400">
                      <input
                        type="checkbox"
                        checked={coverLetterJobs.has(f.name)}
                        onChange={e => {
                          setCoverLetterJobs(prev => {
                            const next = new Set(prev)
                            if (e.target.checked) next.add(f.name)
                            else next.delete(f.name)
                            return next
                          })
                        }}
                        className="rounded"
                      />
                      Cover letter
                    </label>
                    <Tooltip text="Runs AI pipeline with configured provider, falls back to Gemini then deterministic">
                      <button
                        onClick={() => void handleGenerate(f.name)}
                        disabled={b.status === 'running'}
                        className="rounded bg-indigo-700 px-3 py-1 text-xs text-indigo-100 hover:bg-indigo-600 disabled:opacity-50"
                      >
                        {b.status === 'running' ? '…' : 'Generate CV'}
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
                {/* MD content preview */}
                {expandedJob === f.name && (
                  <div className="mt-3 rounded-lg border border-slate-700 bg-slate-950">
                    {expandQ.isLoading ? (
                      <p className="px-3 py-2 text-xs text-slate-500">Loading…</p>
                    ) : (
                      <pre className="max-h-72 overflow-y-auto whitespace-pre-wrap px-4 py-3 font-mono text-xs text-slate-300 leading-relaxed">
                        {expandQ.data?.content ?? ''}
                      </pre>
                    )}
                  </div>
                )}
                {/* PDF preview */}
                {previewJob === f.name && (
                  <iframe
                    src={`/api/out/${cvFileName(f.name)}`}
                    className="h-64 w-full mt-2 rounded"
                    title="CV Preview"
                  />
                )}
                {b.status !== 'idle' && (
                  <BuildProgress
                    build={b}
                    doneExtra={
                      <div className="flex flex-wrap items-center gap-2 mt-1">
                        <a
                          href={`/api/out/${cvFileName(f.name)}`}
                          download
                          className="rounded bg-green-800 px-3 py-1 text-xs font-medium text-green-100 hover:bg-green-700"
                        >
                          ↓ Download PDF
                        </a>
                        <Link to="/output" className="text-xs text-indigo-400 underline">
                          Edit in Generated CVs →
                        </Link>
                      </div>
                    }
                  />
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
