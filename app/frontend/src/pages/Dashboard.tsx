import { useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  getDoctor,
  getLint,
  listJobFiles,
  startBuild,
  uploadCvPdf,
  buildStreamUrl,
} from '../api/client'
import { StatusCard } from '../components/StatusCard'
import { Tooltip } from '../components/Tooltip'

type BuildStatus = 'idle' | 'running' | 'done' | 'error'

type CardBuild = {
  jobId: string | null
  lines: string[]
  status: BuildStatus
}

function useInlineBuild() {
  const [state, setState] = useState<CardBuild>({ jobId: null, lines: [], status: 'idle' })

  const run = async (jobId: string) => {
    setState({ jobId, lines: [], status: 'running' })
    const src = new EventSource(buildStreamUrl(jobId))
    src.onmessage = (e) => {
      if (e.data === '[DONE]') {
        src.close()
        setState(prev => ({ ...prev, status: 'done' }))
      } else {
        setState(prev => ({ ...prev, lines: [...prev.lines, e.data as string] }))
      }
    }
    src.onerror = () => {
      src.close()
      setState(prev => ({ ...prev, status: 'error' }))
    }
  }

  const reset = () => setState({ jobId: null, lines: [], status: 'idle' })

  return { state, run, reset }
}

function InlineLog({ lines, status }: { lines: string[]; status: BuildStatus }) {
  if (status === 'idle') return null
  return (
    <div className="mt-3 max-h-40 overflow-y-auto rounded-lg bg-slate-950 p-3 font-mono text-xs text-slate-300">
      {lines.map((l, i) => <div key={i}>{l}</div>)}
      {status === 'running' && <div className="animate-pulse text-indigo-400">▌</div>}
    </div>
  )
}

export function Dashboard() {
  const navigate = useNavigate()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [selectedJob, setSelectedJob] = useState('')
  const [uploadDone, setUploadDone] = useState(false)
  const [uploadError, setUploadError] = useState(false)

  const doctor = useQuery({ queryKey: ['doctor'], queryFn: getDoctor })
  const lint = useQuery({ queryKey: ['lint'], queryFn: getLint })
  const jobsQ = useQuery({ queryKey: ['files', 'jobs'], queryFn: listJobFiles })

  const genericBuild = useInlineBuild()
  const jobBuild = useInlineBuild()
  const mdBuild = useInlineBuild()

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploadDone(false)
    setUploadError(false)
    try {
      await uploadCvPdf(file)
      setUploadDone(true)
    } catch {
      setUploadError(true)
    }
  }

  const handleGeneric = async () => {
    try {
      const { job_id } = await startBuild({ job: null, llm: 'none' })
      await genericBuild.run(job_id)
    } catch { /* ignore */ }
  }

  const handleJobBuild = async () => {
    if (!selectedJob) return
    try {
      const { job_id } = await startBuild({ job: `jobs/${selectedJob}`, llm: 'none' })
      await jobBuild.run(job_id)
    } catch { /* ignore */ }
  }

  const handleMdBuild = async () => {
    try {
      const { job_id } = await startBuild({ job: null, llm: 'none' })
      await mdBuild.run(job_id)
    } catch { /* ignore */ }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-100">Dashboard</h1>
        <p className="mt-1 text-sm text-slate-400">Quick actions to build and manage your CV</p>
      </div>

      {/* Quick Start */}
      <section>
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-slate-400">
          Quick Start
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">

          {/* Upload my CV (PDF) */}
          <div className="rounded-xl border border-slate-700 bg-slate-900 p-5">
            <div className="mb-2 text-2xl">📄</div>
            <Tooltip text="Upload an existing PDF CV and extract your data automatically into profile files.">
              <h3 className="font-semibold text-slate-100">Upload my CV (PDF)</h3>
            </Tooltip>
            <p className="mt-1 text-xs text-slate-400">Extract data from an existing PDF</p>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={e => void handleFileChange(e)}
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              className="mt-3 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
            >
              Choose PDF…
            </button>
            {uploadDone && (
              <p className="mt-2 text-xs text-green-400">
                Saved!{' '}
                <button onClick={() => navigate('/data')} className="underline">
                  Go to Profile →
                </button>
              </p>
            )}
            {uploadError && (
              <p className="mt-2 text-xs text-red-400">Upload failed. Try again.</p>
            )}
          </div>

          {/* Upload job description */}
          <div className="rounded-xl border border-slate-700 bg-slate-900 p-5">
            <div className="mb-2 text-2xl">💼</div>
            <Tooltip text="Add a job description so the CV builder can tailor your CV to that role.">
              <h3 className="font-semibold text-slate-100">Upload job description</h3>
            </Tooltip>
            <p className="mt-1 text-xs text-slate-400">Add a target job for tailored CVs</p>
            <button
              onClick={() => navigate('/jobs')}
              className="mt-3 rounded-lg bg-slate-700 px-4 py-2 text-sm font-medium text-slate-200 hover:bg-slate-600"
            >
              Go to Target Jobs →
            </button>
          </div>

          {/* Build Generic CV */}
          <div className="rounded-xl border border-slate-700 bg-slate-900 p-5">
            <div className="mb-2 text-2xl">🏗️</div>
            <Tooltip text="Generate a general-purpose CV with no job targeting. Good as a base document.">
              <h3 className="font-semibold text-slate-100">Build Generic CV</h3>
            </Tooltip>
            <p className="mt-1 text-xs text-slate-400">Generate a PDF from your profile data</p>
            <button
              onClick={() => void handleGeneric()}
              disabled={genericBuild.state.status === 'running'}
              className="mt-3 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
            >
              {genericBuild.state.status === 'running' ? 'Building…' : 'Build ⚡'}
            </button>
            {genericBuild.state.status === 'done' && (
              <p className="mt-2 text-xs text-green-400">
                Done!{' '}
                <button onClick={() => navigate('/output')} className="underline">
                  View output →
                </button>
              </p>
            )}
            <InlineLog lines={genericBuild.state.lines} status={genericBuild.state.status} />
          </div>

          {/* Build for Job */}
          <div className="rounded-xl border border-slate-700 bg-slate-900 p-5">
            <div className="mb-2 text-2xl">🎯</div>
            <Tooltip text="Generate a CV tailored to a specific job description you've uploaded.">
              <h3 className="font-semibold text-slate-100">Build for Job</h3>
            </Tooltip>
            <p className="mt-1 text-xs text-slate-400">Target a specific job description</p>
            <div className="mt-3 flex gap-2">
              <select
                value={selectedJob}
                onChange={e => setSelectedJob(e.target.value)}
                className="flex-1 rounded-lg border border-slate-600 bg-slate-800 px-2 py-2 text-sm text-slate-200 outline-none focus:border-indigo-500"
              >
                <option value="">Select job…</option>
                {jobsQ.data?.map(f => (
                  <option key={f.name} value={f.name}>{f.name}</option>
                ))}
              </select>
              <button
                onClick={() => void handleJobBuild()}
                disabled={!selectedJob || jobBuild.state.status === 'running'}
                className="rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
              >
                {jobBuild.state.status === 'running' ? '…' : 'Build ⚡'}
              </button>
            </div>
            {jobBuild.state.status === 'done' && (
              <p className="mt-2 text-xs text-green-400">
                Done!{' '}
                <button onClick={() => navigate('/output')} className="underline">
                  View output →
                </button>
              </p>
            )}
            <InlineLog lines={jobBuild.state.lines} status={jobBuild.state.status} />
          </div>

          {/* Build from Markdowns */}
          <div className="rounded-xl border border-slate-700 bg-slate-900 p-5 sm:col-span-1">
            <div className="mb-2 text-2xl">📝</div>
            <Tooltip text="No LLM — uses your existing markdown files directly. Fastest build option.">
              <h3 className="font-semibold text-slate-100">Build from Markdowns</h3>
            </Tooltip>
            <p className="mt-1 text-xs text-slate-400">Use your markdown files as-is</p>
            <button
              onClick={() => void handleMdBuild()}
              disabled={mdBuild.state.status === 'running'}
              className="mt-3 rounded-lg bg-slate-700 px-4 py-2 text-sm font-medium text-slate-200 hover:bg-slate-600 disabled:opacity-50"
            >
              {mdBuild.state.status === 'running' ? 'Building…' : 'Build ⚡'}
            </button>
            {mdBuild.state.status === 'done' && (
              <p className="mt-2 text-xs text-green-400">
                Done!{' '}
                <button onClick={() => navigate('/output')} className="underline">
                  View output →
                </button>
              </p>
            )}
            <InlineLog lines={mdBuild.state.lines} status={mdBuild.state.status} />
          </div>

        </div>
      </section>

      {/* System Status - collapsed by default */}
      <details className="rounded-xl border border-slate-700 bg-slate-900">
        <summary className="cursor-pointer px-5 py-3 text-sm font-medium uppercase tracking-wide text-slate-400 hover:text-slate-300">
          System Status
        </summary>
        <div className="px-5 pb-5 pt-3 space-y-4">
          {doctor.isLoading && <p className="text-sm text-slate-500">Checking…</p>}
          {doctor.isError && (
            <p className="text-sm text-red-400">Could not reach backend.</p>
          )}
          {doctor.data && (
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {doctor.data.checks.map((c, i) => (
                <StatusCard key={i} check={c} />
              ))}
            </div>
          )}
          {lint.data && (
            <div>
              <p className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-400">Lint</p>
              {lint.data.ok ? (
                <p className="text-sm text-green-400">✓ No issues found.</p>
              ) : (
                <ul className="space-y-1">
                  {lint.data.issues.map((issue, i) => (
                    <li key={i} className="flex gap-2 text-sm">
                      <span className={`shrink-0 font-mono text-xs ${issue.severity === 'ERROR' ? 'text-red-400' : 'text-yellow-400'}`}>
                        {issue.severity}
                      </span>
                      <span className="text-slate-300">{issue.message}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>
      </details>
    </div>
  )
}
