import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  listOutFiles,
  deleteOutFile,
  renameOutFile,
  buildFromMd,
  buildStreamUrl,
} from '../api/client'
import type { FileItem } from '../api/client'
import { FileEditor } from '../components/FileEditor'
import { ConfirmDialog } from '../components/ConfirmDialog'

type BuildState = { lines: string[]; status: 'idle' | 'running' | 'done' | 'error' }

function useRowBuild(onDone: () => void) {
  const [builds, setBuilds] = useState<Record<string, BuildState>>({})

  const run = async (key: string, jobId: string) => {
    setBuilds(prev => ({ ...prev, [key]: { lines: [], status: 'running' } }))
    const src = new EventSource(buildStreamUrl(jobId))
    src.onmessage = (e) => {
      if (e.data === '[DONE]') {
        src.close()
        setBuilds(prev => ({ ...prev, [key]: { ...prev[key], status: 'done' } }))
        onDone()
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
  const [selectedMd, setSelectedMd] = useState<string | null>(null)
  const [draft, setDraft] = useState('')
  const [saved, setSaved] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null)
  const [renaming, setRenaming] = useState<string | null>(null)
  const [renameValue, setRenameValue] = useState('')
  const [saveAsDialog, setSaveAsDialog] = useState<{ original: string; copy: string } | null>(null)

  const listQ = useQuery({ queryKey: ['out'], queryFn: listOutFiles, refetchInterval: 10000 })

  const { builds, run: runBuild } = useRowBuild(() => {
    void qc.invalidateQueries({ queryKey: ['out'] })
  })

  const mdFileQ = useQuery({
    queryKey: ['out-md', selectedMd],
    queryFn: async () => {
      // out/ files served via /api/out/{filename}
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

  const handleSelectMd = (name: string) => {
    setSelectedMd(name)
    setDraft('')
    setSaved(false)
  }

  if (mdFileQ.data && draft === '' && mdFileQ.data.content) {
    setDraft(mdFileQ.data.content)
  }

  const handleSaveMd = () => {
    if (!selectedMd) return
    const isLlmGenerated = !selectedMd.includes('_user')
    if (isLlmGenerated) {
      const copyName = selectedMd.replace(/\.md$/, '_user.md')
      setSaveAsDialog({ original: selectedMd, copy: copyName })
    } else {
      saveMdMut.mutate({ path: selectedMd, content: draft })
    }
  }

  const handleGeneratePdf = async (mdName: string) => {
    try {
      const { job_id } = await buildFromMd(`out/${mdName}`)
      await runBuild(mdName, job_id)
    } catch { /* ignore */ }
  }

  const { pairs, unpairedPdfs } = groupFiles(listQ.data ?? [])

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-0 overflow-hidden rounded-xl border border-slate-700">
      {/* Left panel */}
      <div className="w-80 shrink-0 overflow-y-auto border-r border-slate-700 bg-slate-900">
        <div className="border-b border-slate-700 px-3 py-2 text-xs font-medium uppercase tracking-wide text-slate-400">
          Generated CVs
        </div>

        {listQ.isLoading && <p className="px-3 py-2 text-xs text-slate-500">Loading…</p>}

        {pairs.length === 0 && unpairedPdfs.length === 0 && !listQ.isLoading && (
          <p className="px-3 py-4 text-xs text-slate-500">No output files yet. Run a build on the Dashboard.</p>
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
                    <span className="flex-1 truncate font-mono text-sm text-slate-200">{base}</span>
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
                    onClick={() => handleSelectMd(md.name)}
                    className={`rounded px-2 py-1 text-xs ${selectedMd === md.name ? 'bg-indigo-700 text-indigo-100' : 'bg-slate-700 text-slate-200 hover:bg-slate-600'}`}
                  >
                    Edit MD
                  </button>
                )}
                {md && (
                  <button
                    onClick={() => void handleGeneratePdf(md.name)}
                    disabled={b.status === 'running'}
                    className="rounded bg-indigo-700 px-2 py-1 text-xs text-indigo-100 hover:bg-indigo-600 disabled:opacity-50"
                  >
                    {b.status === 'running' ? '…' : '⚡ PDF'}
                  </button>
                )}
                {pdf && (
                  <a
                    href={`/api/out/${pdf.name}`}
                    download
                    className="rounded bg-slate-700 px-2 py-1 text-xs text-slate-200 hover:bg-slate-600"
                  >
                    ↓ PDF
                  </a>
                )}
                <button
                  onClick={() => setDeleteTarget(pdf?.name ?? md?.name ?? '')}
                  className="rounded bg-red-950 px-2 py-1 text-xs text-red-300 hover:bg-red-900"
                >
                  Delete
                </button>
              </div>

              {/* Inline build log */}
              {b.status !== 'idle' && (
                <div className="mt-2 max-h-24 overflow-y-auto rounded bg-slate-950 p-2 font-mono text-xs text-slate-300">
                  {b.lines.slice(-20).map((l, i) => <div key={i}>{l}</div>)}
                  {b.status === 'running' && <div className="animate-pulse text-indigo-400">▌</div>}
                  {b.status === 'done' && <div className="text-green-400">✓ Done</div>}
                </div>
              )}
            </div>
          )
        })}

        {unpairedPdfs.length > 0 && (
          <div className="border-t border-slate-700 px-3 py-2">
            <p className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">PDF only</p>
            {unpairedPdfs.map(f => (
              <div key={f.name} className="mb-2 flex items-center justify-between">
                <span className="truncate font-mono text-xs text-slate-400">{f.name}</span>
                <div className="flex gap-1">
                  <a href={`/api/out/${f.name}`} download className="rounded bg-slate-700 px-2 py-1 text-xs text-slate-200 hover:bg-slate-600">↓</a>
                  <button onClick={() => setDeleteTarget(f.name)} className="rounded bg-red-950 px-2 py-1 text-xs text-red-300 hover:bg-red-900">×</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Right panel - MD editor */}
      <div className="flex-1 overflow-hidden bg-slate-950">
        {!selectedMd && (
          <div className="flex h-full flex-col items-center justify-center gap-2 text-sm text-slate-500">
            <p>Select "Edit MD" to edit a generated markdown file.</p>
            <p className="text-xs text-slate-600">Tip: edit source data in Profile → Projects for changes across all CVs.</p>
          </div>
        )}
        {selectedMd && mdFileQ.isLoading && (
          <div className="flex h-full items-center justify-center text-sm text-slate-500">Loading…</div>
        )}
        {selectedMd && mdFileQ.data && (
          <FileEditor
            path={selectedMd}
            content={draft || mdFileQ.data.content}
            onChange={v => { setDraft(v); setSaved(false) }}
            onSave={handleSaveMd}
            saving={saveMdMut.isPending}
            saved={saved}
          />
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
    </div>
  )
}
