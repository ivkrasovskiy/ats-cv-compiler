interface Props {
  filename: string | null
}

export function PdfViewer({ filename }: Props) {
  if (!filename) {
    return (
      <div className="flex h-64 items-center justify-center rounded-lg border border-slate-700 bg-slate-900 text-sm text-slate-500">
        PDF preview will appear after a successful build.
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900">
      <div className="flex items-center justify-between border-b border-slate-700 px-4 py-2">
        <span className="font-mono text-sm text-slate-400">{filename}</span>
        <a
          href={`/api/out/${filename}`}
          download
          className="rounded bg-slate-700 px-3 py-1 text-sm text-slate-200 hover:bg-slate-600"
        >
          Download
        </a>
      </div>
      <iframe
        src={`/api/out/${filename}`}
        className="h-[600px] w-full rounded-b-lg"
        title="PDF Preview"
      />
    </div>
  )
}
