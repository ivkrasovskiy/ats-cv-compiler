interface MonthInputProps {
  value: string
  onChange: (v: string) => void
  placeholder?: string
  disabled?: boolean
}

export function MonthInput({ value, onChange, placeholder, disabled }: MonthInputProps) {
  return (
    <div className="flex gap-2">
      <input
        type="month"
        value={value}
        onChange={e => onChange(e.target.value)}
        disabled={disabled}
        placeholder={placeholder}
        className="rounded-lg border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 outline-none focus:border-indigo-500 disabled:opacity-50"
      />
      {value && (
        <button
          type="button"
          onClick={() => onChange('')}
          className="text-xs text-slate-500 hover:text-slate-300"
          title="Clear date"
        >
          ✕
        </button>
      )}
    </div>
  )
}
