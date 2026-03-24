import { useState } from 'react'

function renderMarkdown(md: string): string {
  return md
    .replace(/^---[\s\S]*?---\n*/m, '')
    .replace(/^### (.+)$/gm, '<h3 style="font-size:1rem;font-weight:600;margin:1em 0 0.25em">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 style="font-size:1.15rem;font-weight:700;margin:1.25em 0 0.25em">$1</h2>')
    .replace(/^# (.+)$/gm, '<h1 style="font-size:1.3rem;font-weight:700;margin:1.5em 0 0.25em">$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^- (.+)$/gm, '<li style="margin-left:1.5em;list-style:disc">$1</li>')
    .replace(/\n\n/g, '</p><p style="margin:0.75em 0">')
    .replace(/^(?!<[hlp])(.+)$/gm, '$1')
}

export function MdViewPanel({
  selectedMd,
  content,
  onEdit,
}: {
  selectedMd: string
  content: string
  onEdit: () => void
}) {
  const [preview, setPreview] = useState(false)

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-slate-700 px-4 py-2">
        <span className="font-mono text-sm text-slate-400">{selectedMd}</span>
        <div className="flex gap-2">
          <button
            onClick={() => setPreview(p => !p)}
            className={`rounded px-3 py-1 text-xs ${preview ? 'bg-indigo-700 text-indigo-100' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'}`}
          >
            {preview ? 'Raw' : 'Preview'}
          </button>
          <button
            onClick={onEdit}
            className="rounded bg-indigo-600 px-3 py-1 text-sm text-white hover:bg-indigo-500"
          >
            Edit
          </button>
        </div>
      </div>
      <div className="flex-1 overflow-auto p-4">
        {preview ? (
          <div
            className="text-sm text-slate-200 leading-relaxed"
            dangerouslySetInnerHTML={{ __html: `<p style="margin:0.75em 0">${renderMarkdown(content)}</p>` }}
          />
        ) : (
          <pre className="whitespace-pre-wrap font-mono text-xs text-slate-300">{content}</pre>
        )}
      </div>
    </div>
  )
}
