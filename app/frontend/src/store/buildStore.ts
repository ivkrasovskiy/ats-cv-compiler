import { create } from 'zustand'

interface BuildState {
  jobId: string | null
  status: 'idle' | 'running' | 'done' | 'error'
  lines: string[]
  exitCode: number | null
  setJobId: (id: string) => void
  appendLine: (line: string) => void
  setStatus: (s: BuildState['status'], code?: number | null) => void
  reset: () => void
}

export const useBuildStore = create<BuildState>(set => ({
  jobId: null,
  status: 'idle',
  lines: [],
  exitCode: null,
  setJobId: id => set({ jobId: id, status: 'running', lines: [], exitCode: null }),
  appendLine: line => set(state => ({ lines: [...state.lines, line] })),
  setStatus: (status, exitCode = null) => set({ status, exitCode }),
  reset: () => set({ jobId: null, status: 'idle', lines: [], exitCode: null }),
}))
