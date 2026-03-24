import { useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate, Link } from 'react-router-dom'
import {
  getDoctor,
  getLint,
  listJobFiles,
  startBuild,
  uploadCvPdf,
  ingestPdf,
  getConfig,
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

const PROVIDER_LABELS: Record<string, string> = {
  gemini: 'Gemini CLI',
  claude: 'Claude CLI',
  custom: 'Custom endpoint',
}

function AiProviderNote({ provider }: { provider?: string }) {
  const label = PROVIDER_LABELS[provider ?? ''] ?? 'Gemini CLI'
  const isDefault = !provider || provider === 'gemini'
  return (
    <p className="mt-2 text-xs text-slate-500">
      AI parsing uses <span className="text-slate-400 font-medium">{label}</span>
      {isDefault && ' (default)'}
      {' '}—{' '}
      <a href="/build" className="underline text-indigo-400 hover:text-indigo-300">
        change in Gen Config
      </a>
    </p>
  )
}

export function Dashboard() {
  const navigate = useNavigate()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [selectedJob, setSelectedJob] = useState('')
  const [uploadDone, setUploadDone] = useState(false)
  const [uploadError, setUploadError] = useState(false)
  const [parseState, setParseState] = useState<'idle' | 'running' | 'done' | 'error'>('idle')
  const [parseWarnings, setParseWarnings] = useState<string[]>([])
  const [parseError, setParseError] = useState('')
  const [parseCount, setParseCount] = useState(0)
  const [showSteps, setShowSteps] = useState(() => !localStorage.getItem('ats_onboarded'))

  const doctor = useQuery({ queryKey: ['doctor'], queryFn: getDoctor })
  const lint = useQuery({ queryKey: ['lint'], queryFn: getLint })
  const jobsQ = useQuery({ queryKey: ['files', 'jobs'], queryFn: listJobFiles })
  const configQ = useQuery({ queryKey: ['config'], queryFn: getConfig })
  const authQ = useQuery({
    queryKey: ['agent-auth-status'],
    queryFn: (): Promise<{ provider: string; logged_in: boolean }> =>
      fetch('/api/agent/auth-status').then(r => r.json()),
    staleTime: 30_000,
    retry: false,
  })

  const genericBuild = useInlineBuild()
  const jobBuild = useInlineBuild()

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploadDone(false)
    setUploadError(false)
    setParseState('idle')
    setParseWarnings([])
    setParseError('')
    setParseCount(0)
    try {
      await uploadCvPdf(file)
      setUploadDone(true)
    } catch {
      setUploadError(true)
    }
  }

  const handleParseWithAi = async () => {
    setParseState('running')
    setParseWarnings([])
    setParseError('')
    try {
      const result = await ingestPdf()
      setParseCount(result.written.length)
      setParseWarnings(result.warnings)
      setParseState('done')
    } catch (err) {
      setParseError(err instanceof Error ? err.message : 'Unknown error')
      setParseState('error')
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

  const handleDismissSteps = () => {
    localStorage.setItem('ats_onboarded', '1')
    setShowSteps(false)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-100">Dashboard</h1>
        <p className="mt-1 text-sm text-slate-400">Quick actions to build and manage your CV</p>
      </div>

      {/* Getting Started */}
      {showSteps && (
        <section className="rounded-xl border border-indigo-800 bg-indigo-950/30 p-5">
          <h2 className="mb-3 text-sm font-semibold text-indigo-300">
            Getting Started — follow these steps for your first CV
          </h2>
          <ol className="space-y-2">
            <li className="flex items-start gap-3">
              {authQ.data?.logged_in ? (
                <span className="shrink-0 flex h-6 w-6 items-center justify-center rounded-full bg-green-700 text-xs font-bold text-white">✓</span>
              ) : (
                <span className="shrink-0 flex h-6 w-6 items-center justify-center rounded-full bg-yellow-600 text-xs font-bold text-white">1</span>
              )}
              <span className="text-sm text-slate-300">
                {authQ.data?.logged_in ? (
                  <span className="text-green-400">
                    Logged in to {authQ.data.provider === 'claude' ? 'Claude CLI' : 'Gemini CLI'} ✓
                  </span>
                ) : (
                  <>
                    <strong className="text-yellow-300">Log in to your AI assistant first</strong>
                    {' — '}go to the{' '}
                    <Link to="/agent" className="underline text-indigo-400">Agent tab</Link>,
                    click <strong>Start</strong>, and complete the login prompt
                    {authQ.data?.provider === 'claude'
                      ? ' (Anthropic account)'
                      : ' (Google account for Gemini)'}.
                    {' '}AI features won't work until this is done.
                  </>
                )}
              </span>
            </li>
            <li className="flex items-start gap-3">
              <span className="shrink-0 flex h-6 w-6 items-center justify-center rounded-full bg-indigo-700 text-xs font-bold text-white">2</span>
              <span className="text-sm text-slate-300">
                Upload your existing CV (PDF) — use the <strong>Upload my CV</strong> card below
              </span>
            </li>
            <li className="flex items-start gap-3">
              <span className="shrink-0 flex h-6 w-6 items-center justify-center rounded-full bg-indigo-700 text-xs font-bold text-white">3</span>
              <span className="text-sm text-slate-300">
                Review &amp; edit your Profile —{' '}
                <Link to="/data" className="underline text-indigo-400">go to Profile tab</Link>
              </span>
            </li>
            <li className="flex items-start gap-3">
              <span className="shrink-0 flex h-6 w-6 items-center justify-center rounded-full bg-indigo-700 text-xs font-bold text-white">4</span>
              <span className="text-sm text-slate-300">
                Add target job descriptions —{' '}
                <Link to="/jobs" className="underline text-indigo-400">go to Target Jobs tab</Link>
              </span>
            </li>
            <li className="flex items-start gap-3">
              <span className="shrink-0 flex h-6 w-6 items-center justify-center rounded-full bg-indigo-700 text-xs font-bold text-white">5</span>
              <span className="text-sm text-slate-300">
                Generate your CVs — use <strong>Build for Job</strong> or <strong>Build Generic CV</strong> cards below
              </span>
            </li>
          </ol>
          <button
            onClick={handleDismissSteps}
            className="mt-4 rounded-lg border border-indigo-700 px-4 py-1.5 text-xs text-indigo-300 hover:bg-indigo-900/40"
          >
            Got it, don't show again
          </button>
        </section>
      )}

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
            <AiProviderNote provider={configQ.data?.basic['CV_AI_PROVIDER']} />
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={e => void handleFileChange(e)}
            />
            {!uploadDone ? (
              <button
                onClick={() => fileInputRef.current?.click()}
                className="mt-3 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
              >
                Choose PDF…
              </button>
            ) : (
              <div className="mt-3 space-y-2">
                <p className="text-xs text-green-400">✓ Saved</p>
                {parseState === 'idle' && (
                  <button
                    onClick={() => void handleParseWithAi()}
                    className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
                  >
                    Parse with AI →
                  </button>
                )}
                {parseState === 'running' && (
                  <p className="text-xs text-slate-400 animate-pulse">⏳ Parsing your CV…</p>
                )}
                {parseState === 'done' && (
                  <div className="mt-2 space-y-2">
                    <p className="text-xs text-green-400">✓ {parseCount} files created</p>
                    {parseWarnings.length > 0 && (
                      <ul className="mb-1 space-y-0.5">
                        {parseWarnings.map((w, i) => (
                          <li key={i} className="text-xs text-yellow-400">⚠ {w}</li>
                        ))}
                      </ul>
                    )}
                    <p className="text-xs font-medium text-slate-300">Review each section before building:</p>
                    <ol className="space-y-1">
                      {[
                        { to: '/data?tab=profile', label: 'Profile — name, headline, links' },
                        { to: '/data?tab=skills', label: 'Skills — categories & items' },
                        { to: '/data?tab=education', label: 'Education & languages' },
                        { to: '/data?tab=projects', label: 'Projects — dates, bullets, tags' },
                      ].map(({ to, label }, i) => (
                        <li key={i} className="flex items-center gap-2 text-xs text-slate-400">
                          <span className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-indigo-800 text-[10px] font-bold text-white">{i + 1}</span>
                          <button onClick={() => navigate(to)} className="underline text-indigo-400 hover:text-indigo-300 text-left">{label}</button>
                        </li>
                      ))}
                    </ol>
                    <p className="text-xs text-slate-500">Then come back here to build your CV ↓</p>
                  </div>
                )}
                {parseState === 'error' && (
                  <div>
                    <p className="text-xs text-red-400">✗ Parse failed: {parseError}</p>
                    <button
                      onClick={() => void handleParseWithAi()}
                      className="mt-1 rounded bg-slate-700 px-3 py-1 text-xs text-slate-300 hover:bg-slate-600"
                    >
                      Retry
                    </button>
                  </div>
                )}
              </div>
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

          {/* Agent Terminal */}
          <div className="rounded-xl border border-slate-700 bg-slate-900 p-5">
            <div className="mb-2 text-2xl">🤖</div>
            <Tooltip text="Open a live terminal connected to Claude or Gemini. Ask questions, edit CV data, debug build errors — all from the browser.">
              <h3 className="font-semibold text-slate-100">Agent Terminal</h3>
            </Tooltip>
            <p className="mt-1 text-xs text-slate-400">
              Talk to Claude or Gemini directly from the browser
            </p>
            <ul className="mt-2 space-y-0.5 text-xs text-slate-500">
              <li>· Edit profile, skills, or experience by chatting</li>
              <li>· Debug a failed build or lint error</li>
              <li>· Ask the AI to tailor your CV for a job</li>
            </ul>
            <button
              onClick={() => navigate('/agent')}
              className="mt-3 rounded-lg bg-slate-700 px-4 py-2 text-sm font-medium text-slate-200 hover:bg-slate-600"
            >
              Open Agent →
            </button>
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
                {jobsQ.data?.filter(f => f.name.toLowerCase() !== 'readme.md').map(f => (
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
