import type { ReactNode } from 'react'

interface TooltipProps {
  text: string
  children: ReactNode
}

export function Tooltip({ text, children }: TooltipProps) {
  return (
    <span className="group/tooltip relative inline-flex items-center gap-1">
      {children}
      <span className="inline-flex h-4 w-4 cursor-default items-center justify-center rounded-full bg-slate-700 text-xs text-slate-400 hover:bg-slate-600 hover:text-slate-200">
        ?
      </span>
      <span className="pointer-events-none absolute bottom-full left-1/2 z-50 mb-2 w-64 -translate-x-1/2 rounded-lg bg-slate-800 px-3 py-2 text-xs text-slate-200 opacity-0 shadow-lg ring-1 ring-slate-700 transition-opacity group-hover/tooltip:opacity-100">
        {text}
        <span className="absolute left-1/2 top-full -translate-x-1/2 border-4 border-transparent border-t-slate-800" />
      </span>
    </span>
  )
}
