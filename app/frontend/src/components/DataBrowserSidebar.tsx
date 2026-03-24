import type { FileItem } from '../api/client'
import { stripPrefix, groupByCompany } from '../utils/dataBrowserUtils'

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

export function Section({
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

export function GroupedSection({
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
