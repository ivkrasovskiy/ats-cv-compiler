import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listDataFiles, getDataFile, putDataFile } from '../api/client'
import { FileTree } from '../components/FileTree'
import { FileEditor } from '../components/FileEditor'

export function DataBrowser() {
  const qc = useQueryClient()
  const [selected, setSelected] = useState<string | null>(null)
  const [draft, setDraft] = useState<string>('')
  const [saved, setSaved] = useState(false)

  const treeQ = useQuery({ queryKey: ['files', 'data'], queryFn: listDataFiles })

  const fileQ = useQuery({
    queryKey: ['file', 'data', selected],
    queryFn: () => getDataFile(selected!),
    enabled: selected !== null,
    staleTime: Infinity,
  })

  // When a new file loads, reset draft
  const handleSelect = (path: string) => {
    setSelected(path)
    setSaved(false)
  }

  // Keep draft in sync when file first loads
  if (fileQ.data && draft === '' && fileQ.data.content) {
    setDraft(fileQ.data.content)
  }

  const saveMut = useMutation({
    mutationFn: () => putDataFile(selected!, draft),
    onSuccess: () => {
      setSaved(true)
      void qc.invalidateQueries({ queryKey: ['files', 'data'] })
      setTimeout(() => setSaved(false), 2000)
    },
  })

  const handleSelect2 = (path: string) => {
    handleSelect(path)
    // Reset draft to trigger sync on next file load
    setDraft('')
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-0 overflow-hidden rounded-xl border border-slate-700">
      {/* Left panel */}
      <div className="w-56 shrink-0 overflow-y-auto border-r border-slate-700 bg-slate-900">
        <div className="border-b border-slate-700 px-3 py-2 text-xs font-medium uppercase tracking-wide text-slate-400">
          data/
        </div>
        {treeQ.isLoading && <p className="px-3 py-2 text-xs text-slate-500">Loading…</p>}
        {treeQ.data && (
          <FileTree files={treeQ.data} selected={selected} onSelect={handleSelect2} />
        )}
      </div>

      {/* Right panel */}
      <div className="flex-1 overflow-hidden bg-slate-950">
        {!selected && (
          <div className="flex h-full items-center justify-center text-sm text-slate-500">
            Select a file to edit.
          </div>
        )}
        {selected && fileQ.isLoading && (
          <div className="flex h-full items-center justify-center text-sm text-slate-500">
            Loading…
          </div>
        )}
        {selected && fileQ.data && (
          <FileEditor
            path={selected}
            content={draft || fileQ.data.content}
            onChange={v => {
              setDraft(v)
              setSaved(false)
            }}
            onSave={() => saveMut.mutate()}
            saving={saveMut.isPending}
            saved={saved}
          />
        )}
      </div>
    </div>
  )
}
