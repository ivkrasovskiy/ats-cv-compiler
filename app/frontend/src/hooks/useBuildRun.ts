import { useEffect, useState } from 'react'
import { buildStreamUrl } from '../api/client'
import { getBuilds, updateBuild, subscribe } from '../stores/buildStore'

// Lines matching this pattern carry step progress metadata — not shown in the log.
const STEP_RE = /^\[STEP (\d+)\/(\d+)\] (.+)$/

function applyLine(key: string, line: string): boolean {
  const m = line.match(STEP_RE)
  if (m) {
    updateBuild(key, prev => ({
      ...prev,
      currentStep: parseInt(m[1]),
      totalSteps: parseInt(m[2]),
      stepName: m[3],
    }))
    return true // marker consumed, don't add to visible lines
  }
  return false
}

export function useBuildRun(onDone?: () => void) {
  const [, forceUpdate] = useState(0)

  useEffect(() => subscribe(() => forceUpdate(n => n + 1)), [])

  const run = (key: string, jobId: string, doneCb?: () => void) => {
    updateBuild(key, () => ({
      lines: [],
      status: 'running',
      totalSteps: 0,
      currentStep: 0,
      stepName: '',
    }))

    const src = new EventSource(buildStreamUrl(jobId))

    src.onmessage = e => {
      if (e.data === '[DONE]') {
        src.close()
        updateBuild(key, prev => ({ ...prev, status: 'done' }))
        ;(doneCb ?? onDone)?.()
      } else {
        const line: string = e.data
        const isMarker = applyLine(key, line)
        if (!isMarker) {
          updateBuild(key, prev => ({ ...prev, lines: [...prev.lines, line] }))
        }
      }
    }

    src.onerror = () => {
      src.close()
      updateBuild(key, prev => ({ ...prev, status: 'error' }))
    }
  }

  return { builds: getBuilds(), run }
}
