import { useState, useMemo, useCallback } from 'react'
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
import { CvSectionEditor } from '../components/CvSectionEditor'
import { PdfViewer } from '../components/PdfViewer'
import { MdViewPanel } from '../components/MdViewPanel'
import { OutputFileList } from '../components/OutputFileList'
import { OutputDialogs } from '../components/OutputDialogs'
import { useBuildRun } from '../hooks/useBuildRun'
import { groupFiles } from '../utils/outputUtils'
import type { FilePair } from '../utils/outputUtils'

type RightMode = 'none' | 'pdf' | 'md-view' | 'editor'

export function OutputPage() {
  const qc = useQueryClient()

  const [rightMode, setRightMode] = useState<RightMode>('none')
  const [previewPdf, setPreviewPdf] = useState<string | null>(null)
  const [selectedMd, setSelectedMd] = useState<string | null>(null)
  const [draft, setDraft] = useState('')
  const [isDirty, setIsDirty] = useState(false)
  const [saved, setSaved] = useState(false)
  const [sectionMode, setSectionMode] = useState(true)
  const [showEditorSplit, setShowEditorSplit] = useState(false)
  const [pdfVersion, setPdfVersion] = useState(0)
  const [leftCollapsed, setLeftCollapsed] = useState(false)

  const [deleteTarget, setDeleteTarget] = useState<string | null>(null)
  const [renaming, setRenaming] = useState<string | null>(null)
  const [renameValue, setRenameValue] = useState('')
  const [saveAsDialog, setSaveAsDialog] = useState<{ original: string; copy: string } | null>(null)
  const [pendingRowSwitch, setPendingRowSwitch] = useState<{ pdf: string | null; md: string | null; mode?: 'editor' | 'md-view' } | null>(null)
  const [discardCancelDialog, setDiscardCancelDialog] = useState(false)
  const [regenDropdown, setRegenDropdown] = useState<{ pair: FilePair; md: string; top: number; left: number } | null>(null)

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
        setSelectedMd(null); setDraft(''); setIsDirty(false); setRightMode('none')
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
      setSelectedMd(md); setDraft(''); setIsDirty(false); setSaved(false)
      setPreviewPdf(pdf); setRightMode(mode)
    } else {
      setPreviewPdf(pdf); setRightMode(pdf ? 'pdf' : 'none')
      setSelectedMd(null); setDraft(''); setIsDirty(false); setSaved(false)
    }
  }

  const handleRowClick = (pdf: FileItem) => {
    if (isDirty) { setPendingRowSwitch({ pdf: pdf.name, md: null }); return }
    doRowSwitch(pdf.name, null)
  }

  const handleViewMd = (md: FileItem) => {
    if (isDirty) { setPendingRowSwitch({ pdf: previewPdf, md: md.name, mode: 'md-view' }); return }
    setSelectedMd(md.name); setDraft(''); setIsDirty(false); setSaved(false); setRightMode('md-view')
  }

  const handleEditMd = (md: FileItem) => {
    if (isDirty && selectedMd !== md.name) {
      setPendingRowSwitch({ pdf: previewPdf, md: md.name, mode: 'editor' }); return
    }
    setSelectedMd(md.name); setDraft(''); setIsDirty(false); setSaved(false); setRightMode('editor')
  }

  if (mdFileQ.data && draft === '' && mdFileQ.data.content) {
    setDraft(mdFileQ.data.content)
  }

  const handleRerenderMd = async (mdName: string) => {
    try {
      const { job_id } = await buildFromMd(`out/${mdName}`)
      await runBuild(mdName, job_id)
    } catch { /* ignore */ }
  }

  const handleSaveMd = async () => {
    if (!selectedMd) return
    const isLlmGenerated = !selectedMd.includes('_user')
    if (isLlmGenerated) {
      const copyName = selectedMd.replace(/\.md$/, '_user.md')
      setSaveAsDialog({ original: selectedMd, copy: copyName }); return
    }
    await saveMdMut.mutateAsync({ path: selectedMd, content: draft })
    setShowEditorSplit(true); setLeftCollapsed(true)
    void handleRerenderMd(selectedMd)
  }

  const toggleSplit = () => {
    setShowEditorSplit(s => {
      const next = !s
      if (next) setLeftCollapsed(true); else setLeftCollapsed(false)
      return next
    })
  }

  const handleRegenPreview = async () => {
    if (!selectedMd) return
    if (isDirty) {
      const isLlmGenerated = !selectedMd.includes('_user')
      if (isLlmGenerated) {
        const copyName = selectedMd.replace(/\.md$/, '_user.md')
        await saveMdMut.mutateAsync({ path: copyName, content: draft })
        setSelectedMd(copyName)
      } else {
        await saveMdMut.mutateAsync({ path: selectedMd, content: draft })
      }
    }
    setShowEditorSplit(true); setLeftCollapsed(true)
    void handleRerenderMd(selectedMd)
  }

  const handleCancelEdit = () => {
    if (isDirty) { setDiscardCancelDialog(true); return }
    setShowEditorSplit(false); setLeftCollapsed(false)
    setSelectedMd(null); setDraft(''); setRightMode(previewPdf ? 'pdf' : 'none')
  }

  const jobPathForBase = (base: string): string | null => {
    if (base.startsWith('cv_job_')) return `jobs/${base.replace(/^cv_job_/, '')}.md`
    if (base !== 'cv_generic' && base.startsWith('cv_')) return `jobs/${base.replace(/^cv_/, '')}.md`
    return null
  }

  const handleGenerateAuto = async (base: string, mdName: string) => {
    try {
      const jobPath = jobPathForBase(base)
      const { job_id } = await startBuild({ job: jobPath, llm: 'auto' })
      await runBuild(mdName, job_id)
    } catch { /* ignore */ }
  }

  const { pairs, unpairedPdfs } = useMemo(() => groupFiles(listQ.data ?? []), [listQ.data])
  const handleEditorChange = useCallback((v: string) => {
    setDraft(v); setIsDirty(true); setSaved(false)
  }, [])

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-0 overflow-hidden rounded-xl border border-slate-700">
      {/* Left panel */}
      <div className={`shrink-0 overflow-y-auto border-r border-slate-700 bg-slate-900 transition-[width] duration-200 ${leftCollapsed ? 'w-8' : 'w-64'}`}>
        <OutputFileList
          pairs={pairs}
          unpairedPdfs={unpairedPdfs}
          builds={builds}
          selectedMd={selectedMd}
          rightMode={rightMode}
          isLoading={listQ.isLoading}
          leftCollapsed={leftCollapsed}
          renaming={renaming}
          renameValue={renameValue}
          onCollapse={setLeftCollapsed}
          onRowClick={handleRowClick}
          onViewMd={handleViewMd}
          onEditMd={handleEditMd}
          onGenerateAuto={(base, mdName) => void handleGenerateAuto(base, mdName)}
          onSetDeleteTarget={setDeleteTarget}
          onSetRenaming={setRenaming}
          onSetRenameValue={setRenameValue}
          onRename={(from, to) => renameMut.mutate({ from, to })}
          onRegenDropdown={(pair, md, top, left) =>
            setRegenDropdown(prev => prev?.md === md ? null : { pair, md, top, left })
          }
        />
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
          <MdViewPanel
            selectedMd={selectedMd}
            content={mdFileQ.data.content}
            onEdit={() => handleEditMd({ name: selectedMd, path: selectedMd, size: 0 })}
          />
        )}
        {rightMode === 'editor' && selectedMd && mdFileQ.isLoading && (
          <div className="flex h-full items-center justify-center text-sm text-slate-500">Loading…</div>
        )}
        {rightMode === 'editor' && selectedMd && mdFileQ.data && (
          <div className="flex h-full overflow-hidden">
            <div className={`flex flex-col overflow-hidden ${showEditorSplit ? 'w-1/2 border-r border-slate-700' : 'w-full'}`}>
              {(() => {
                const editorContent = draft || mdFileQ.data.content
                const extraActions = (
                  <>
                    <button
                      onClick={() => setSectionMode(m => !m)}
                      className={`rounded px-2 py-1 text-xs hover:bg-slate-600 ${sectionMode ? 'bg-indigo-800 text-indigo-200' : 'bg-slate-700 text-slate-300'}`}
                    >
                      {sectionMode ? '§ Sections' : '§ Raw'}
                    </button>
                    <button
                      onClick={() => void handleRegenPreview()}
                      disabled={builds[selectedMd]?.status === 'running'}
                      className="rounded bg-slate-700 px-2 py-1 text-xs text-slate-300 hover:bg-slate-600 disabled:opacity-50"
                    >
                      {builds[selectedMd]?.status === 'running' ? '⟳ Building…' : '⟳ Regen'}
                    </button>
                    <button
                      onClick={toggleSplit}
                      className={`rounded px-2 py-1 text-xs hover:bg-slate-600 ${showEditorSplit ? 'bg-indigo-800 text-indigo-200' : 'bg-slate-700 text-slate-300'}`}
                    >
                      {showEditorSplit ? '⊟ PDF' : '⊞ PDF'}
                    </button>
                  </>
                )
                return sectionMode ? (
                  <CvSectionEditor
                    key={selectedMd}
                    content={editorContent}
                    onChange={handleEditorChange}
                    onSave={() => void handleSaveMd()}
                    onCancel={handleCancelEdit}
                    saving={saveMdMut.isPending}
                    saved={saved}
                    extraActions={extraActions}
                  />
                ) : (
                  <FileEditor
                    path={selectedMd}
                    content={editorContent}
                    onChange={handleEditorChange}
                    onSave={() => void handleSaveMd()}
                    onCancel={handleCancelEdit}
                    saving={saveMdMut.isPending}
                    saved={saved}
                    extraActions={extraActions}
                  />
                )
              })()}
            </div>
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

      <OutputDialogs
        deleteTarget={deleteTarget}
        saveAsDialog={saveAsDialog}
        pendingRowSwitch={pendingRowSwitch}
        discardCancelDialog={discardCancelDialog}
        regenDropdown={regenDropdown}
        previewPdf={previewPdf}
        onDelete={name => deleteMut.mutate(name)}
        onCancelDelete={() => setDeleteTarget(null)}
        onSaveAsCopy={(original, copy) => {
          renameMut.mutate({ from: original, to: copy })
          saveMdMut.mutate({ path: copy, content: draft })
        }}
        onSaveAsOriginal={original => saveMdMut.mutate({ path: original, content: draft })}
        onConfirmRowSwitch={() => {
          const pr = pendingRowSwitch!
          setPendingRowSwitch(null)
          doRowSwitch(pr.pdf, pr.md, pr.mode)
        }}
        onCancelRowSwitch={() => setPendingRowSwitch(null)}
        onConfirmDiscard={() => {
          setDiscardCancelDialog(false); setShowEditorSplit(false); setLeftCollapsed(false)
          setSelectedMd(null); setDraft(''); setIsDirty(false)
          setRightMode(previewPdf ? 'pdf' : 'none')
        }}
        onCancelDiscard={() => setDiscardCancelDialog(false)}
        onRegenAuto={(base, md) => void handleGenerateAuto(base, md)}
        onRerender={md => void handleRerenderMd(md)}
        onCloseRegen={() => setRegenDropdown(null)}
      />
    </div>
  )
}
