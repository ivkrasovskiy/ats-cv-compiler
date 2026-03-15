const BASE = '/api'

export interface FileItem {
  path: string
  name: string
  size: number
}

export interface BuildRequest {
  job: string | null
  llm: string
}

export interface BuildJob {
  job_id: string
  status: 'running' | 'done' | 'error'
  exit_code: number | null
}

export interface DoctorCheck {
  label: string
  ok: boolean
  raw: string
}

export interface LintIssue {
  message: string
  severity: 'ERROR' | 'WARNING' | 'INFO'
}

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json() as Promise<T>
}

// ── health ────────────────────────────────────────────────────────────────────
export const health = () =>
  fetch(`${BASE}/health`).then(r => json<{ status: string }>(r))

// ── doctor ────────────────────────────────────────────────────────────────────
export const getDoctor = () =>
  fetch(`${BASE}/doctor`).then(r => json<{ checks: DoctorCheck[]; all_ok: boolean }>(r))

// ── lint ──────────────────────────────────────────────────────────────────────
export const getLint = () =>
  fetch(`${BASE}/lint`).then(r => json<{ issues: LintIssue[]; ok: boolean; exit_code: number }>(r))

// ── files/data ────────────────────────────────────────────────────────────────
export const listDataFiles = () =>
  fetch(`${BASE}/files/data`).then(r => json<FileItem[]>(r))

export const getDataFile = (path: string) =>
  fetch(`${BASE}/files/data/${path}`).then(r => json<{ path: string; content: string }>(r))

export const putDataFile = (path: string, content: string) =>
  fetch(`${BASE}/files/data/${path}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
  }).then(r => json<{ path: string; saved: boolean }>(r))

// ── files/jobs ────────────────────────────────────────────────────────────────
export const listJobFiles = () =>
  fetch(`${BASE}/files/jobs`).then(r => json<FileItem[]>(r))

export const getJobFile = (name: string) =>
  fetch(`${BASE}/files/jobs/${name}`).then(r => json<{ name: string; content: string }>(r))

export const putJobFile = (name: string, content: string) =>
  fetch(`${BASE}/files/jobs/${name}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
  }).then(r => json<{ name: string; saved: boolean }>(r))

export const deleteJobFile = (name: string) =>
  fetch(`${BASE}/files/jobs/${name}`, { method: 'DELETE' }).then(r =>
    json<{ name: string; deleted: boolean }>(r),
  )

// ── out ───────────────────────────────────────────────────────────────────────
export const listOutFiles = () =>
  fetch(`${BASE}/out`).then(r => json<FileItem[]>(r))

// ── build ─────────────────────────────────────────────────────────────────────
export const startBuild = (req: BuildRequest) =>
  fetch(`${BASE}/build`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  }).then(r => json<{ job_id: string }>(r))

export const getBuildStatus = (jobId: string) =>
  fetch(`${BASE}/build/${jobId}`).then(r => json<BuildJob>(r))

export const buildStreamUrl = (jobId: string) => `${BASE}/build/${jobId}/stream`
