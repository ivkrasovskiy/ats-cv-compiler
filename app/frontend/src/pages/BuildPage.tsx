import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { listJobFiles, startBuild } from '../api/client'
import { useBuildStore } from '../store/buildStore'
import { useBuildStream } from '../hooks/useBuildStream'
import { BuildLog } from '../components/BuildLog'
import { PdfViewer } from '../components/PdfViewer'

const LLM_OPTIONS = ['none', 'agents', 'openai']

export function BuildPage() {
  const [selectedJob, setSelectedJob] = useState<string>('')
  const [llm, setLlm] = useState('none')

  const { jobId, status, lines, setJobId, setStatus } = useBuildStore()
  useBuildStream(jobId)

  const jobsQ = useQuery({ queryKey: ['files', 'jobs'], queryFn: listJobFiles })

  const handleBuild = async () => {
    setStatus('idle')
    try {
      const { job_id } = await startBuild({
        job: selectedJob || null,
        llm,
      })
      setJobId(job_id)
    } catch {
      setStatus('error')
    }
  }

  // Detect PDF filename from log lines
  const pdfLine = lines.find(l => l.includes('.pdf'))
  const pdfFilename = pdfLine ? /(\S+\.pdf)/.exec(pdfLine)?.[1]?.split('/').pop() ?? null : null

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-100">Build CV</h1>
        <p className="mt-1 text-sm text-slate-400">Generate a PDF from your career data</p>
      </div>

      {/* Build form */}
      <div className="rounded-xl border border-slate-700 bg-slate-900 p-5">
        <div className="flex flex-wrap items-end gap-4">
          <div className="flex-1 min-w-40">
            <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-400">
              Job (optional)
            </label>
            <select
              value={selectedJob}
              onChange={e => setSelectedJob(e.target.value)}
              className="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-slate-200 outline-none focus:border-indigo-500"
            >
              <option value="">Generic (no job)</option>
              {jobsQ.data?.map(f => (
                <option key={f.name} value={`jobs/${f.name}`}>
                  {f.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-400">
              LLM
            </label>
            <select
              value={llm}
              onChange={e => setLlm(e.target.value)}
              className="rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-slate-200 outline-none focus:border-indigo-500"
            >
              {LLM_OPTIONS.map(o => (
                <option key={o} value={o}>
                  {o}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={() => void handleBuild()}
            disabled={status === 'running'}
            className="rounded-lg bg-indigo-600 px-5 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
          >
            {status === 'running' ? 'Building…' : 'Start Build'}
          </button>
        </div>
      </div>

      <BuildLog lines={lines} status={status} />

      {status === 'done' && <PdfViewer filename={pdfFilename} />}
    </div>
  )
}
