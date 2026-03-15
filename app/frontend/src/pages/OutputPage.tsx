import { useQuery } from '@tanstack/react-query'
import { listOutFiles } from '../api/client'
import { PdfViewer } from '../components/PdfViewer'
import { useState } from 'react'

export function OutputPage() {
  const [previewing, setPreviewing] = useState<string | null>(null)
  const listQ = useQuery({ queryKey: ['out'], queryFn: listOutFiles, refetchInterval: 5000 })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-100">Output Files</h1>
        <p className="mt-1 text-sm text-slate-400">Generated CVs in out/</p>
      </div>

      {listQ.isLoading && <p className="text-sm text-slate-500">Loading…</p>}

      {listQ.data?.length === 0 && (
        <p className="text-sm text-slate-500">
          No output files yet. Run a build on the Build page.
        </p>
      )}

      {listQ.data && listQ.data.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-slate-700">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700 bg-slate-900">
                <th className="px-4 py-2 text-left font-medium text-slate-400">Filename</th>
                <th className="px-4 py-2 text-right font-medium text-slate-400">Size</th>
                <th className="px-4 py-2 text-right font-medium text-slate-400">Actions</th>
              </tr>
            </thead>
            <tbody>
              {listQ.data.map(f => (
                <tr key={f.path} className="border-b border-slate-800 bg-slate-900 last:border-0">
                  <td className="px-4 py-2 font-mono text-slate-300">{f.name}</td>
                  <td className="px-4 py-2 text-right text-slate-500">
                    {(f.size / 1024).toFixed(1)} KB
                  </td>
                  <td className="px-4 py-2 text-right">
                    <div className="flex justify-end gap-2">
                      <button
                        onClick={() => setPreviewing(previewing === f.name ? null : f.name)}
                        className="rounded bg-slate-700 px-3 py-1 text-xs text-slate-200 hover:bg-slate-600"
                      >
                        {previewing === f.name ? 'Hide' : 'Preview'}
                      </button>
                      <a
                        href={`/api/out/${f.name}`}
                        download
                        className="rounded bg-indigo-700 px-3 py-1 text-xs text-indigo-100 hover:bg-indigo-600"
                      >
                        Download
                      </a>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {previewing && (
        <div className="mt-4">
          <PdfViewer filename={previewing} />
        </div>
      )}
    </div>
  )
}
