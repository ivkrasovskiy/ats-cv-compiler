const BASE = '/api'

export interface FileItem {
  path: string
  name: string
  size: number
  company?: string
}

export interface BuildRequest {
  job: string | null
  llm: string
  cover_letter?: boolean
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

// ── delete/rename data files ───────────────────────────────────────────────
export const deleteDataFile = (path: string) =>
  fetch(`${BASE}/files/data/${path}`, { method: 'DELETE' }).then(r =>
    json<{ path: string; deleted: boolean }>(r),
  )

// ── delete/rename out files ────────────────────────────────────────────────
export const deleteOutFile = (name: string) =>
  fetch(`${BASE}/out/${name}`, { method: 'DELETE' }).then(r =>
    json<{ filename: string; deleted: boolean }>(r),
  )

export const renameOutFile = (from: string, to: string) =>
  fetch(`${BASE}/out/rename`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ from, to }),
  }).then(r => json<{ from: string; to: string; renamed: boolean }>(r))

// ── build from md ──────────────────────────────────────────────────────────
export const buildFromMd = (md_path: string) =>
  fetch(`${BASE}/build/from-md`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ md_path }),
  }).then(r => json<{ job_id: string }>(r))

// ── config ─────────────────────────────────────────────────────────────────
export interface ConfigData {
  basic: Record<string, string>
  advanced_llm: Record<string, string>
  advanced_timeouts: Record<string, string>
}

export const getConfig = () =>
  fetch(`${BASE}/config`).then(r => json<ConfigData>(r))

export const putConfig = (data: ConfigData) =>
  fetch(`${BASE}/config`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }).then(r => json<{ saved: boolean }>(r))

// ── prompts ────────────────────────────────────────────────────────────────
export const listPrompts = () =>
  fetch(`${BASE}/files/prompts`).then(r => json<FileItem[]>(r))

export const getPrompt = (path: string) =>
  fetch(`${BASE}/files/prompts/${path}`).then(r => json<{ path: string; content: string }>(r))

export const putPrompt = (path: string, content: string) =>
  fetch(`${BASE}/files/prompts/${path}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
  }).then(r => json<{ path: string; saved: boolean }>(r))

// ── upload cv pdf ──────────────────────────────────────────────────────────
export const uploadCvPdf = (file: File) => {
  const form = new FormData()
  form.append('file', file)
  return fetch(`${BASE}/upload/cv-pdf`, { method: 'POST', body: form }).then(r =>
    json<{ saved: boolean; path: string }>(r),
  )
}

// ── form API (structured data file editing) ────────────────────────────────
export const getDataFileForm = (path: string) =>
  fetch(`${BASE}/files/data/${path}/form`).then(r => json<{ type: string; fields: Record<string, unknown> }>(r))

export const putDataFileForm = (path: string, fields: Record<string, unknown>) =>
  fetch(`${BASE}/files/data/${path}/form`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ fields }),
  }).then(r => json<{ path: string; saved: boolean }>(r))

// ── ingest pdf ─────────────────────────────────────────────────────────────
export const ingestPdf = () =>
  fetch(`${BASE}/ingest/pdf`, { method: 'POST' }).then(r =>
    json<{ written: string[]; warnings: string[] }>(r),
  )
