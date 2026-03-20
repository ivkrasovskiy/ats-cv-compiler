import type { FileItem } from '../api/client'

interface Props {
  files: FileItem[]
  selected: string | null
  onSelect: (path: string) => void
}

export function FileTree({ files, selected, onSelect }: Props) {
  if (files.length === 0) {
    return <p className="px-3 py-4 text-sm text-slate-500">No files found.</p>
  }

  return (
    <ul className="py-2">
      {files.map(f => (
        <li key={f.path}>
          <button
            onClick={() => onSelect(f.path)}
            className={`w-full truncate px-3 py-1.5 text-left text-sm transition-colors ${
              selected === f.path
                ? 'bg-indigo-900 text-indigo-200'
                : 'text-slate-300 hover:bg-slate-800'
            }`}
          >
            {f.path}
          </button>
        </li>
      ))}
    </ul>
  )
}
