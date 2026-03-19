import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  listOutFiles,
  deleteOutFile,
  renameOutFile,
  buildFromMd,
  startBuild,
} from '../api/client'
import type { FileItem } from '../api/client'
import { FileEditor } from '../components/FileEditor'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { PdfViewer } from '../components/PdfViewer'
import { useBuildRun } from '../hooks/useBuildRun'
import { BuildProgress } from '../components/BuildProgress'

interface FilePair {
  base: string
  md: FileItem | null
  pdf: FileItem | null
}

function groupFiles(files: FileItem[]): { pairs: FilePair[]; unpairedPdfs: FileItem[] } {
  const mdMap = new Map<string, FileItem>()
  const pdfMap = new Map<string, FileItem>()

  for (const f of files) {
    if (f.name.endsWith('.md')) {
      mdMap.set(f.name.replace(/\.md$/, ''), f)
    } else if (f.name.endsWith('.pdf')) {
      pdfMap.set(f.name.replace(/\.pdf$/, ''), f)
    }
  }

  const allBases = new Set([...mdMap.keys(), ...pdfMap.keys()])
  const pairs: FilePair[] = []
  const unpairedPdfs: FileItem[] = []

  for (const base of allBases) {
    const md = mdMap.get(base) ?? null
    const pdf = pdfMap.get(base) ?? null
    if (md || pdf) {
      if (!md && pdf) {
        unpairedPdfs.push(pdf)
      } else {
        pairs.push({ base, md, pdf })
      }
    }
  }

  pairs.sort((a, b) => a.base.localeCompare(b.base))
  return { pairs, unpairedPdfs }
}

export function OutputPage() {
  const qc = useQueryClient()

  // Right panel state
  const [rightMode, setRightMode] = useState<'none' | 'pdf' | 'md-view' | 'editor'>('none')
  const [previewPdf, setPreviewPdf] = useState<string | null>(null)
  const [selectedMd, setSelectedMd] = useState<string | null>(null)
  const [draft, setDraft] = useState('')
  const [isDirty, setIsDirty] = useState(false)
  const [saved, setSaved] = useState(false)

  // Editor split-view state
  const [showEditorSplit, setShowEditorSplit] = useState(false)
  const [pdfVersion, setPdfVersion] = useState(0)
  const [leftCollapsed, setLeftCollapsed] = useState(false)

  // Dialogs / UI state
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null)
  const [renaming, setRenaming] = useState<string | null>(null)
  const [renameValue, setRenameValue] = useState('')
  const [saveAsDialog, setSaveAsDialog] = useState<{ original: string; copy: string } | null>(null)
  const [pendingRowSwitch, setPendingRowSwitch] = useState<{ pdf: string | null; md: string | null; mode?: 'editor' | 'md-view' } | null>(null)
  const [discardCancelDialog, setDiscardCancelDialog] = useState(false)
  const [regenOpen, setRegenOpen] = useState<string | null>(null)

  const listQ = useQuery({ queryKey: ['out'], queryFn: listOutFiles, refetchInterval: 10000 })

  const { builds, run } = useBuildRun()
  const runBuild = (key: string, jobId: string) => run(key, jobId, () => {
    void qc.invalidateQueries({ queryKey: ['out'] })
    setPdfVersion(v => v + 1)
  })

  const mdFileQ = useQuery({
    queryKey: ['out-md', selectedMd],
    queryFn: async () => {
      const res = await fetch(`/api/out/${selectedMd}`)
      if (!res.ok) throw new Error('Failed to load')
      const text = await res.text()
      return { path: selectedMd!, content: text }
    },
    enabled: selectedMd !== null,
    staleTime: Infinity,
  })

  const saveMdMut = useMutation({
    mutationFn: async ({ path, content }: { path: string; content: string }) => {
      const res = await fetch(`/api/out/${path}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content }),
      })
      if (!res.ok) throw new Error('Save failed')
      return res.json()
    },
    onSuccess: () => {
      setSaved(true)
      setIsDirty(false)
      setSaveAsDialog(null)
      void qc.invalidateQueries({ queryKey: ['out'] })
      setTimeout(() => setSaved(false), 2000)
    },
  })

  const deleteMut = useMutation({
    mutationFn: (name: string) => deleteOutFile(name),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['out'] })
      setDeleteTarget(null)
      if (selectedMd === deleteTarget) {
        setSelectedMd(null)
        setDraft('')
        setIsDirty(false)
        setRightMode('none')
      }
    },
  })

  const renameMut = useMutation({
    mutationFn: ({ from, to }: { from: string; to: string }) => renameOutFile(from, to),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['out'] })
      setRenaming(null)
      setRenameValue('')
    },
  })

  const doRowSwitch = (pdf: string | null, md: string | null, mode: 'editor' | 'md-view' = 'editor') => {
    setShowEditorSplit(false)
    setLeftCollapsed(false)
    if (md) {
      setSelectedMd(md)
      setDraft('')
      setIsDirty(false)
      setSaved(false)
      setPreviewPdf(pdf)
      setRightMode(mode)
    } else {
      setPreviewPdf(pdf)
      setRightMode(pdf ? 'pdf' : 'none')
      setSelectedMd(null)
      setDraft('')
      setIsDirty(false)
      setSaved(false)
    }
  }

  const handleRowClick = (pdf: FileItem) => {
    if (isDirty) {
      setPendingRowSwitch({ pdf: pdf.name, md: null })
      return
    }
    doRowSwitch(pdf.name, null)
  }

  const handleViewMd = (md: FileItem) => {
    if (isDirty) {
      setPendingRowSwitch({ pdf: previewPdf, md: md.name, mode: 'md-view' })
      return
    }
    setSelectedMd(md.name)
    setDraft('')
    setIsDirty(false)
    setSaved(false)
    setRightMode('md-view')
  }

  const handleEditMd = (md: FileItem) => {
    if (isDirty && selectedMd !== md.name) {
      setPendingRowSwitch({ pdf: previewPdf, md: md.name, mode: 'editor' })
      return
    }
    setSelectedMd(md.name)
    setDraft('')
    setIsDirty(false)
    setSaved(false)
    setRightMode('editor')
  }

  if (mdFileQ.data && draft === '' && mdFileQ.data.content) {
    setDraft(mdFileQ.data.content)
  }

  const handleSaveMd = async () => {
    if (!selectedMd) return
    const isLlmGenerated = !selectedMd.includes('_user')
    if (isLlmGenerated) {
      const copyName = selectedMd.replace(/\.md$/, '_user.md')
      setSaveAsDialog({ original: selectedMd, copy: copyName })
      return
    }
    await saveMdMut.mutateAsync({ path: selectedMd, content: draft })
    // auto-regen and open split view
    setShowEditorSplit(true)
    setLeftCollapsed(true)
    void handleGeneratePdf(selectedMd)
  }

  const toggleSplit = () => {
    setShowEditorSplit(s => {
      const next = !s
      if (next) setLeftCollapsed(true)   // auto-collapse left when opening split
      else setLeftCollapsed(false)        // restore left when closing split
      return next
    })
  }

  const handleRegenPreview = async () => {
    if (!selectedMd) return
    // save draft first if dirty
    if (isDirty) {
      const isLlmGenerated = !selectedMd.includes('_user')
      if (isLlmGenerated) {
        // for LLM files, save to _user copy silently
        const copyName = selectedMd.replace(/\.md$/, '_user.md')
        await saveMdMut.mutateAsync({ path: copyName, content: draft })
        setSelectedMd(copyName)
      } else {
        await saveMdMut.mutateAsync({ path: selectedMd, content: draft })
      }
    }
    setShowEditorSplit(true)
    setLeftCollapsed(true)
    void handleGeneratePdf(selectedMd)
  }

  const handleCancelEdit = () => {
    if (isDirty) {
      setDiscardCancelDialog(true)
    } else {
      setShowEditorSplit(false)
      setLeftCollapsed(false)
      setSelectedMd(null)
      setDraft('')
      setRightMode(previewPdf ? 'pdf' : 'none')
    }
  }

  // Re-render the edited markdown file directly to PDF (no AI, no pipeline re-run)
  const handleRerenderMd = async (mdName: string) => {
    try {
      const { job_id } = await buildFromMd(`out/${mdName}`)
      await runBuild(mdName, job_id)
    } catch { /* ignore */ }
  }

  // Derive the job path from the CV base name, e.g. cv_job_google → jobs/google.md
  const jobPathForBase = (base: string): string | null => {
    if (base.startsWith('cv_job_')) return `jobs/${base.replace(/^cv_job_/, '')}.md`
    return null
  }

  // Run the full pipeline with auto AI-provider fallback (configured → Gemini → deterministic)
  const handleGenerateAuto = async (base: string, mdName: string) => {
    try {
      const jobPath = jobPathForBase(base)
      const { job_id } = await startBuild({ job: jobPath, llm: 'auto' })
      await runBuild(mdName, job_id)
    } catch { /* ignore */ }
  }

  const { pairs, unpairedPdfs } = groupFiles(listQ.data ?? [])

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-0 overflow-hidden rounded-xl border border-slate-700">
      {/* Left panel */}
      <div className={`shrink-0 overflow-y-auto border-r border-slate-700 bg-slate-900 transition-[width] duration-200 ${leftCollapsed ? 'w-8' : 'w-64'}`}>
        {leftCollapsed ? (
          <div className="flex h-full flex-col items-center pt-2">
            <button
              onClick={() => setLeftCollapsed(false)}
              className="rounded p-1 text-slate-500 hover:text-slate-300"
              title="Expand file list"
            >
              ▶
            </button>
          </div>
        ) : (
        <><div className="flex items-center justify-between border-b border-slate-700 px-3 py-2">
          <span className="text-xs font-medium uppercase tracking-wide text-slate-400">Generated CVs</span>
          <button
            onClick={() => setLeftCollapsed(true)}
            className="text-xs text-slate-600 hover:text-slate-400"
            title="Collapse file list"
          >
            ◀
          </button>
        </div>

        {listQ.isLoading && <p className="px-3 py-2 text-xs text-slate-500">Loading…</p>}

        {pairs.length === 0 && unpairedPdfs.length === 0 && !listQ.isLoading && (
          <p className="px-3 py-4 text-xs text-slate-500">
            No CVs yet.{' '}
            <Link to="/jobs" className="underline text-indigo-400">Go to Target Jobs</Link>
            {' '}and click "Generate CV" to create one.
          </p>
        )}

        {pairs.map(({ base, md, pdf }) => {
          const b = builds[md?.name ?? ''] ?? { lines: [], status: 'idle' }
          return (
            <div key={base} className="border-b border-slate-800 px-3 py-3">
              {/* Filename + rename */}
              <div className="flex items-center gap-1 mb-2">
                {renaming === base ? (
                  <div className="flex flex-1 gap-1">
                    <input
                      autoFocus
                      value={renameValue}
                      onChange={e => setRenameValue(e.target.value)}
                      onKeyDown={e => {
                        if (e.key === 'Enter' && pdf) {
                          const newName = renameValue.endsWith('.pdf') ? renameValue : `${renameValue}.pdf`
                          renameMut.mutate({ from: pdf.name, to: newName })
                        }
                      }}
                      className="flex-1 rounded border border-slate-600 bg-slate-800 px-2 py-0.5 text-xs text-slate-200 outline-none"
                    />
                    <button onClick={() => setRenaming(null)} className="text-xs text-slate-500">✕</button>
                  </div>
                ) : (
                  <>
                    <button
                      className="flex-1 truncate text-left font-mono text-sm text-slate-200 hover:text-indigo-300"
                      onClick={() => pdf && handleRowClick(pdf)}
                      title={base}
                    >
                      {base}
                    </button>
                    <button
                      onClick={() => { setRenaming(base); setRenameValue(base) }}
                      className="shrink-0 text-xs text-slate-500 hover:text-slate-300"
                      title="Rename"
                    >
                      ✏️
                    </button>
                  </>
                )}
              </div>

              {/* Actions */}
              <div className="flex flex-wrap gap-1">
                {md && (
                  <button
                    onClick={() => handleViewMd(md)}
                    className={`rounded px-2 py-1 text-xs ${selectedMd === md.name && rightMode === 'md-view' ? 'bg-slate-600 text-slate-100' : 'bg-slate-700 text-slate-200 hover:bg-slate-600'}`}
                  >
                    View MD
                  </button>
                )}
                {md && (
                  <button
                    onClick={() => handleEditMd(md)}
                    className={`rounded px-2 py-1 text-xs ${selectedMd === md.name && rightMode === 'editor' ? 'bg-indigo-700 text-indigo-100' : 'bg-slate-700 text-slate-200 hover:bg-slate-600'}`}
                  >
                    Edit MD
                  </button>
                )}
                {md && (
                  <div className="relative flex">
                    <button
                      onClick={() => void handleGenerateAuto(base, md.name)}
                      disabled={b.status === 'running'}
                      className="rounded-l bg-indigo-700 px-2 py-1 text-xs text-indigo-100 hover:bg-indigo-600 disabled:opacity-50"
                    >
                      {b.status === 'running' ? '…' : 'Generate CV'}
                    </button>
                    <button
                      onClick={() => setRegenOpen(regenOpen === md.name ? null : md.name)}
                      className="rounded-r border-l border-indigo-900 bg-indigo-700 px-1 py-1 text-xs text-indigo-100 hover:bg-indigo-600"
                    >
                      ▾
                    </button>
                    {regenOpen === md.name && (
                      <div className="absolute right-0 top-full z-50 mt-1 w-64 rounded border border-slate-600 bg-slate-800 shadow-lg">
                        <button
                          onClick={() => { void handleGenerateAuto(base, md.name); setRegenOpen(null) }}
                          className="block w-full px-3 py-2 text-left hover:bg-slate-700"
                        >
                          <div className="text-xs font-medium text-slate-200">Generate CV</div>
                          <div className="mt-0.5 text-xs text-slate-500">Run AI pipeline (configured provider → Gemini → original bullets)</div>
                        </button>
                        <button
                          onClick={() => { void handleRerenderMd(md.name); setRegenOpen(null) }}
                          className="block w-full border-t border-slate-700 px-3 py-2 text-left hover:bg-slate-700"
                        >
                          <div className="text-xs font-medium text-slate-200">Rerender MD→PDF</div>
                          <div className="mt-0.5 text-xs text-slate-500">Convert the edited markdown to PDF — fast, no AI</div>
                        </button>
                      </div>
                    )}
                  </div>
                )}
                <button
                  onClick={() => setDeleteTarget(pdf?.name ?? md?.name ?? '')}
                  className="rounded bg-red-950 px-2 py-1 text-xs text-red-300 hover:bg-red-900"
                >
                  Delete
                </button>
              </div>

              {b.status !== 'idle' && (
                <BuildProgress build={b} className="mt-2" />
              )}
            </div>
          )
        })}

        {unpairedPdfs.length > 0 && (
          <div className="border-t border-slate-700 px-3 py-2">
            <p className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">PDF only</p>
            {unpairedPdfs.map(f => (
              <div key={f.name} className="mb-2 flex items-center justify-between">
                <button
                  className="truncate font-mono text-xs text-slate-400 hover:text-indigo-300"
                  onClick={() => handleRowClick(f)}
                  title={f.name}
                >
                  {f.name}
                </button>
                <button
                  onClick={() => setDeleteTarget(f.name)}
                  className="rounded bg-red-950 px-2 py-1 text-xs text-red-300 hover:bg-red-900"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}
        </>)}
      </div>

      {/* Right panel */}
      <div className="flex-1 overflow-hidden bg-slate-950">
        {rightMode === 'none' && (
          <div className="flex h-full flex-col items-center justify-center gap-2 px-6 text-center">
            {pairs.length === 0 && unpairedPdfs.length === 0 && !listQ.isLoading ? (
              <>
                <p className="text-base text-slate-300">No CVs generated yet.</p>
                <p className="text-sm text-slate-500">
                  Go to{' '}
                  <Link to="/jobs" className="underline text-indigo-400">Target Jobs</Link>
                  {' '}and click "Generate CV" to create your first one.
                </p>
              </>
            ) : (
              <>
                <p className="text-base text-slate-200">Click a file name to preview its PDF.</p>
                <p className="text-sm text-slate-400">Tip: click "Edit MD" to edit the source markdown before regenerating.</p>
              </>
            )}
          </div>
        )}
        {rightMode === 'pdf' && (
          <div className="h-full overflow-auto p-4">
            <PdfViewer filename={previewPdf} />
          </div>
        )}
        {rightMode === 'md-view' && selectedMd && mdFileQ.isLoading && (
          <div className="flex h-full items-center justify-center text-sm text-slate-500">Loading…</div>
        )}
        {rightMode === 'md-view' && selectedMd && mdFileQ.data && (
          <div className="flex h-full flex-col">
            <div className="flex items-center justify-between border-b border-slate-700 px-4 py-2">
              <span className="font-mono text-sm text-slate-400">{selectedMd}</span>
              <button
                onClick={() => handleEditMd({ name: selectedMd, path: selectedMd, size: 0 })}
                className="rounded bg-indigo-600 px-3 py-1 text-sm text-white hover:bg-indigo-500"
              >
                Edit
              </button>
            </div>
            <div className="flex-1 overflow-auto p-4">
              <pre className="whitespace-pre-wrap font-mono text-xs text-slate-300">{mdFileQ.data.content}</pre>
            </div>
          </div>
        )}
        {rightMode === 'editor' && selectedMd && mdFileQ.isLoading && (
          <div className="flex h-full items-center justify-center text-sm text-slate-500">Loading…</div>
        )}
        {rightMode === 'editor' && selectedMd && mdFileQ.data && (
          <div className="flex h-full overflow-hidden">
            {/* Editor pane */}
            <div className={`flex flex-col overflow-hidden ${showEditorSplit ? 'w-1/2 border-r border-slate-700' : 'w-full'}`}>
              <FileEditor
                path={selectedMd}
                content={draft || mdFileQ.data.content}
                onChange={v => { setDraft(v); setIsDirty(true); setSaved(false) }}
                onSave={() => void handleSaveMd()}
                onCancel={handleCancelEdit}
                saving={saveMdMut.isPending}
                saved={saved}
                extraActions={
                  <>
                    <button
                      onClick={() => void handleRegenPreview()}
                      disabled={builds[selectedMd]?.status === 'running'}
                      className="rounded bg-slate-700 px-2 py-1 text-xs text-slate-300 hover:bg-slate-600 disabled:opacity-50"
                      title="Save draft and regenerate PDF preview"
                    >
                      {builds[selectedMd]?.status === 'running' ? '⟳ Building…' : '⟳ Regen'}
                    </button>
                    <button
                      onClick={toggleSplit}
                      className={`rounded px-2 py-1 text-xs hover:bg-slate-600 ${showEditorSplit ? 'bg-indigo-800 text-indigo-200' : 'bg-slate-700 text-slate-300'}`}
                      title={showEditorSplit ? 'Hide PDF panel' : 'Show PDF panel'}
                    >
                      {showEditorSplit ? '⊟ PDF' : '⊞ PDF'}
                    </button>
                  </>
                }
              />
            </div>
            {/* PDF preview pane */}
            {showEditorSplit && (
              <div className="flex w-1/2 flex-col overflow-hidden">
                <div className="flex shrink-0 items-center justify-between border-b border-slate-700 px-3 py-2">
                  <span className="text-xs text-slate-400">
                    PDF Preview
                    {isDirty && <span className="ml-2 text-yellow-400">— unsaved changes not reflected</span>}
                  </span>
                  {builds[selectedMd]?.status === 'running' && (
                    <span className="animate-pulse text-xs text-indigo-400">Building…</span>
                  )}
                  {builds[selectedMd]?.status === 'done' && (
                    <span className="text-xs text-green-400">✓ Up to date</span>
                  )}
                </div>
                <div className="flex-1 overflow-hidden">
                  {previewPdf ? (
                    <iframe
                      key={pdfVersion}
                      src={`/api/out/${previewPdf}?v=${pdfVersion}`}
                      className="h-full w-full"
                      title="PDF Preview"
                    />
                  ) : (
                    <div className="flex h-full items-center justify-center text-xs text-slate-500">
                      No PDF yet — click ⟳ Regen to generate
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Confirm delete */}
      {deleteTarget && (
        <ConfirmDialog
          title="Delete file?"
          message={`Delete "${deleteTarget}"? This cannot be undone.`}
          confirmLabel="Delete"
          onConfirm={() => deleteMut.mutate(deleteTarget)}
          onCancel={() => setDeleteTarget(null)}
        />
      )}

      {/* Save-as dialog for LLM-generated files */}
      {saveAsDialog && (
        <ConfirmDialog
          title="Save as user-edited copy?"
          message={`Save as "${saveAsDialog.copy}" to prevent overwriting on regeneration, or overwrite the original "${saveAsDialog.original}".`}
          confirmLabel="Save as copy"
          cancelLabel="Overwrite original"
          onConfirm={() => {
            renameMut.mutate({ from: saveAsDialog.original, to: saveAsDialog.copy })
            saveMdMut.mutate({ path: saveAsDialog.copy, content: draft })
          }}
          onCancel={() => saveMdMut.mutate({ path: saveAsDialog.original, content: draft })}
        />
      )}

      {/* Unsaved changes on row switch */}
      {pendingRowSwitch && (
        <ConfirmDialog
          title="Unsaved changes"
          message="You have unsaved changes. Discard them and switch?"
          confirmLabel="Discard"
          cancelLabel="Keep editing"
          onConfirm={() => {
            const pr = pendingRowSwitch
            setPendingRowSwitch(null)
            doRowSwitch(pr.pdf, pr.md, pr.mode)
          }}
          onCancel={() => setPendingRowSwitch(null)}
        />
      )}

      {/* Discard changes on cancel */}
      {discardCancelDialog && (
        <ConfirmDialog
          title="Discard changes?"
          message="Your unsaved changes will be lost."
          confirmLabel="Discard"
          cancelLabel="Keep editing"
          onConfirm={() => {
            setDiscardCancelDialog(false)
            setShowEditorSplit(false)
            setLeftCollapsed(false)
            setSelectedMd(null)
            setDraft('')
            setIsDirty(false)
            setRightMode(previewPdf ? 'pdf' : 'none')
          }}
          onCancel={() => setDiscardCancelDialog(false)}
        />
      )}
    </div>
  )
}
