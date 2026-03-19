/**
 * Module-level build state store.
 * Lives outside React so it survives tab navigation (component unmount/remount).
 */

export type BuildStatus = 'idle' | 'running' | 'done' | 'error'

export interface BuildState {
  lines: string[]
  status: BuildStatus
  totalSteps: number
  currentStep: number
  stepName: string
}

const DEFAULT: BuildState = {
  lines: [],
  status: 'idle',
  totalSteps: 0,
  currentStep: 0,
  stepName: '',
}

const _builds: Record<string, BuildState> = {}
const _listeners = new Set<() => void>()

export function getBuild(key: string): BuildState {
  return _builds[key] ?? DEFAULT
}

export function getBuilds(): Record<string, BuildState> {
  return _builds
}

export function updateBuild(key: string, updater: (prev: BuildState) => BuildState): void {
  _builds[key] = updater(_builds[key] ?? { ...DEFAULT })
  _listeners.forEach(l => l())
}

export function subscribe(listener: () => void): () => void {
  _listeners.add(listener)
  return () => _listeners.delete(listener)
}
