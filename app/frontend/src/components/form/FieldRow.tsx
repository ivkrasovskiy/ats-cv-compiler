interface FieldRowProps {
  label: string
  error?: string
  children: React.ReactNode
  hint?: string
}

export function FieldRow({ label, error, children, hint }: FieldRowProps) {
  return (
    <div className="space-y-1">
      <label className="block text-sm font-medium text-slate-300">{label}</label>
      {children}
      {hint && !error && <p className="text-xs text-slate-500">{hint}</p>}
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  )
}
