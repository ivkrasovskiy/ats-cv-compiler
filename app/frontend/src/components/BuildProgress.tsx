import type { ReactNode } from 'react'
import type { BuildState } from '../stores/buildStore'

interface Props {
  build: BuildState
  className?: string
  doneExtra?: ReactNode
}

export function BuildProgress({ build, className = '', doneExtra }: Props) {
  const { lines, status, totalSteps, currentStep, stepName } = build
  const hasSteps = totalSteps > 0

  const pct = hasSteps
    ? status === 'done'
      ? 100
      : Math.round((currentStep / totalSteps) * 100)
    : null

  const stepLabel = status === 'done'
    ? 'Done'
    : stepName || (status === 'running' ? 'Working…' : '')

  return (
    <div className={`rounded bg-slate-950 p-2 font-mono text-xs text-slate-300 ${className}`}>
      {/* Progress bar — only for auto-mode builds that emit step markers */}
      {hasSteps && (
        <div className="mb-2">
          <div className="mb-1 flex items-center justify-between gap-2">
            <span className={`truncate ${status === 'done' ? 'text-green-400' : status === 'error' ? 'text-red-400' : 'text-indigo-300'}`}>
              {status === 'done' ? '✓' : status === 'error' ? '✗' : '⟳'} {stepLabel}
            </span>
            <span className="shrink-0 text-slate-500">
              {status === 'done' ? `${totalSteps}/${totalSteps}` : `${currentStep}/${totalSteps}`}
            </span>
          </div>
          <div className="h-1.5 w-full overflow-hidden rounded bg-slate-700">
            <div
              className={`h-full rounded transition-all duration-500 ${
                status === 'error' ? 'bg-red-600' : 'bg-indigo-500'
              }`}
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>
      )}

      {/* Raw log lines (warnings, output paths, errors) */}
      {lines.length > 0 && (
        <div className="max-h-24 overflow-y-auto">
          {lines.slice(-30).map((l, i) => (
            <div
              key={i}
              className={
                l.startsWith('[⚠]') ? 'text-yellow-400' :
                l.startsWith('[→]') ? 'text-slate-400' :
                l.startsWith('ERROR') || l.startsWith('✗') ? 'text-red-400' :
                'text-slate-300'
              }
            >
              {l}
            </div>
          ))}
        </div>
      )}

      {/* Status line when no step markers and no log lines */}
      {!hasSteps && lines.length === 0 && status === 'running' && (
        <div className="animate-pulse text-indigo-400">Working…</div>
      )}

      {/* Fallback status for non-step builds */}
      {!hasSteps && status === 'running' && (
        <div className="animate-pulse text-indigo-400">▌</div>
      )}
      {!hasSteps && status === 'done' && (
        <div className="text-green-400">✓ Done</div>
      )}
      {status === 'error' && !hasSteps && (
        <div className="text-red-400">
          ✗ Build failed{lines.length === 0 && ' — check that your AI tool (gemini/claude) is installed and authenticated'}
        </div>
      )}

      {/* Extra content shown after successful build (e.g. download button) */}
      {status === 'done' && doneExtra}
    </div>
  )
}
