import { Link } from 'react-router-dom'
import type { FileItem } from '../api/client'
import type { FilePair } from '../utils/outputUtils'
import { BuildProgress } from './BuildProgress'
import type { BuildState } from '../stores/buildStore'

interface Props {
  pairs: FilePair[]
  unpairedPdfs: FileItem[]
  builds: Record<string, BuildState>
  selectedMd: string | null
  rightMode: string
  isLoading: boolean
  leftCollapsed: boolean
  renaming: string | null
  renameValue: string
  sortOrder: 'newest' | 'oldest' | 'alpha'
  onSortChange: (order: 'newest' | 'oldest' | 'alpha') => void
  onCollapse: (v: boolean) => void
  onRowClick: (pdf: FileItem) => void
  onViewMd: (md: FileItem) => void
  onEditMd: (md: FileItem) => void
  onGenerateAuto: (base: string, mdName: string) => void
  onSetDeleteTarget: (name: string) => void
  onSetRenaming: (base: string | null) => void
  onSetRenameValue: (v: string) => void
  onRename: (from: string, to: string) => void
  onRegenDropdown: (pair: FilePair, md: string, top: number, left: number) => void
}

export function OutputFileList({
  pairs,
  unpairedPdfs,
  builds,
  selectedMd,
  rightMode,
  isLoading,
  leftCollapsed,
  renaming,
  renameValue,
  sortOrder,
  onSortChange,
  onCollapse,
  onRowClick,
  onViewMd,
  onEditMd,
  onGenerateAuto,
  onSetDeleteTarget,
  onSetRenaming,
  onSetRenameValue,
  onRename,
  onRegenDropdown,
}: Props) {
  if (leftCollapsed) {
    return (
      <div className="flex h-full flex-col items-center pt-2">
        <button
          onClick={() => onCollapse(false)}
          className="rounded p-1 text-slate-500 hover:text-slate-300"
          title="Expand file list"
        >
          ▶
        </button>
      </div>
    )
  }

  return (
    <>
      <div className="flex items-center justify-between border-b border-slate-700 px-3 py-2">
        <span className="text-xs font-medium uppercase tracking-wide text-slate-400">Generated CVs</span>
        <div className="flex items-center gap-1">
          <select
            value={sortOrder}
            onChange={e => onSortChange(e.target.value as 'newest' | 'oldest' | 'alpha')}
            className="rounded border border-slate-700 bg-slate-800 px-1 py-0.5 text-xs text-slate-400 outline-none focus:border-indigo-500"
          >
            <option value="newest">Newest</option>
            <option value="oldest">Oldest</option>
            <option value="alpha">A–Z</option>
          </select>
          <button
            onClick={() => onCollapse(true)}
            className="text-xs text-slate-600 hover:text-slate-400"
            title="Collapse file list"
          >
            ◀
          </button>
        </div>
      </div>

      {isLoading && <p className="px-3 py-2 text-xs text-slate-500">Loading…</p>}

      {pairs.length === 0 && unpairedPdfs.length === 0 && !isLoading && (
        <p className="px-3 py-4 text-xs text-slate-500">
          No CVs yet.{' '}
          <Link to="/jobs" className="underline text-indigo-400">Go to Target Jobs</Link>
          {' '}and click "Generate CV" to create one.
        </p>
      )}

      {pairs.map(({ base, md, pdf, coverLetter }) => {
        const b = builds[md?.name ?? ''] ?? { lines: [], status: 'idle' }
        return (
          <div key={base} className="border-b border-slate-800 px-3 py-3">
            <div className="flex items-center gap-1 mb-2">
              {renaming === base ? (
                <div className="flex flex-1 gap-1">
                  <input
                    autoFocus
                    value={renameValue}
                    onChange={e => onSetRenameValue(e.target.value)}
                    onKeyDown={e => {
                      if (e.key === 'Enter' && pdf) {
                        const newName = renameValue.endsWith('.pdf') ? renameValue : `${renameValue}.pdf`
                        onRename(pdf.name, newName)
                      }
                    }}
                    className="flex-1 rounded border border-slate-600 bg-slate-800 px-2 py-0.5 text-xs text-slate-200 outline-none"
                  />
                  <button onClick={() => onSetRenaming(null)} className="text-xs text-slate-500">✕</button>
                </div>
              ) : (
                <>
                  <button
                    className="flex-1 truncate text-left font-mono text-sm text-slate-200 hover:text-indigo-300"
                    onClick={() => pdf && onRowClick(pdf)}
                    title={base}
                  >
                    {base}
                  </button>
                  <button
                    onClick={() => { onSetRenaming(base); onSetRenameValue(base) }}
                    className="shrink-0 text-xs text-slate-500 hover:text-slate-300"
                    title="Rename"
                  >
                    ✏️
                  </button>
                </>
              )}
            </div>

            <div className="flex flex-wrap gap-1">
              {coverLetter && (
                <button
                  onClick={() => onViewMd(coverLetter)}
                  className="rounded px-2 py-1 text-xs bg-slate-700 text-slate-200 hover:bg-slate-600"
                  title="View cover letter"
                >
                  Cover letter
                </button>
              )}
              {md && (
                <button
                  onClick={() => onViewMd(md)}
                  className={`rounded px-2 py-1 text-xs ${selectedMd === md.name && rightMode === 'md-view' ? 'bg-slate-600 text-slate-100' : 'bg-slate-700 text-slate-200 hover:bg-slate-600'}`}
                >
                  View MD
                </button>
              )}
              {md && (
                <button
                  onClick={() => onEditMd(md)}
                  className={`rounded px-2 py-1 text-xs ${selectedMd === md.name && rightMode === 'editor' ? 'bg-indigo-700 text-indigo-100' : 'bg-slate-700 text-slate-200 hover:bg-slate-600'}`}
                >
                  Edit MD
                </button>
              )}
              {md && (
                <div className="flex">
                  <button
                    onClick={() => onGenerateAuto(base, md.name)}
                    disabled={b.status === 'running'}
                    className="rounded-l bg-indigo-700 px-2 py-1 text-xs text-indigo-100 hover:bg-indigo-600 disabled:opacity-50"
                  >
                    {b.status === 'running' ? '…' : 'Generate CV'}
                  </button>
                  <button
                    onClick={e => {
                      const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
                      onRegenDropdown({ base, md, pdf, coverLetter }, md.name, rect.bottom + 4, rect.left - 192)
                    }}
                    className="rounded-r border-l border-indigo-900 bg-indigo-700 px-1 py-1 text-xs text-indigo-100 hover:bg-indigo-600"
                  >
                    ▾
                  </button>
                </div>
              )}
              <button
                onClick={() => onSetDeleteTarget(pdf?.name ?? md?.name ?? '')}
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
                onClick={() => onRowClick(f)}
                title={f.name}
              >
                {f.name}
              </button>
              <button
                onClick={() => onSetDeleteTarget(f.name)}
                className="rounded bg-red-950 px-2 py-1 text-xs text-red-300 hover:bg-red-900"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}
    </>
  )
}
