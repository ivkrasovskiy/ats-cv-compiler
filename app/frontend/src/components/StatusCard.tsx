import type { DoctorCheck } from '../api/client'

interface Props {
  check: DoctorCheck
}

export function StatusCard({ check }: Props) {
  return (
    <div
      className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-sm ${
        check.ok
          ? 'border-green-800 bg-green-950 text-green-300'
          : 'border-red-800 bg-red-950 text-red-300'
      }`}
    >
      <span className="shrink-0">{check.ok ? '✓' : '✗'}</span>
      <span className="truncate">{check.label}</span>
      {!check.ok && (
        <span className="ml-auto shrink-0 rounded bg-red-800 px-1.5 py-0.5 text-xs font-mono text-red-100">
          ERROR
        </span>
      )}
    </div>
  )
}
