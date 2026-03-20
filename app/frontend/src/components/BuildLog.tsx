import { useEffect, useRef } from 'react'

interface Props {
  lines: string[]
  status: 'idle' | 'running' | 'done' | 'error'
}

export function BuildLog({ lines, status }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [lines])

  if (status === 'idle') {
    return (
      <div className="flex h-40 items-center justify-center rounded-lg border border-slate-700 bg-slate-900 text-sm text-slate-500">
        Build log will appear here.
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900">
      <div className="flex items-center justify-between border-b border-slate-700 px-4 py-2">
        <span className="text-sm font-medium text-slate-300">Build Log</span>
        <span
          className={`rounded px-2 py-0.5 text-xs font-mono ${
            status === 'running'
              ? 'bg-yellow-900 text-yellow-300'
              : status === 'done'
                ? 'bg-green-900 text-green-300'
                : 'bg-red-900 text-red-300'
          }`}
        >
          {status}
        </span>
      </div>
      <div className="max-h-72 overflow-y-auto p-4 font-mono text-sm">
        {lines.map((line, i) => (
          <div key={i} className="text-slate-300">
            {line || '\u00A0'}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
