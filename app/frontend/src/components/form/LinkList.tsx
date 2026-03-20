interface LinkItem {
  label: string
  url: string
}

interface LinkListProps {
  value: LinkItem[]
  onChange: (links: LinkItem[]) => void
}

export function LinkList({ value, onChange }: LinkListProps) {
  const update = (index: number, field: 'label' | 'url', text: string) => {
    const next = value.map((item, i) => i === index ? { ...item, [field]: text } : item)
    onChange(next)
  }

  const remove = (index: number) => {
    onChange(value.filter((_, i) => i !== index))
  }

  const add = () => {
    onChange([...value, { label: '', url: '' }])
  }

  return (
    <div className="space-y-2">
      {value.map((link, i) => (
        <div key={i} className="flex items-center gap-2">
          <input
            type="text"
            value={link.label}
            onChange={e => update(i, 'label', e.target.value)}
            placeholder="Label"
            className="w-28 rounded-lg border border-slate-600 bg-slate-800 px-2 py-1.5 text-sm text-slate-200 placeholder-slate-500 outline-none focus:border-indigo-500"
          />
          <input
            type="url"
            value={link.url}
            onChange={e => update(i, 'url', e.target.value)}
            placeholder="https://…"
            className="flex-1 rounded-lg border border-slate-600 bg-slate-800 px-2 py-1.5 text-sm text-slate-200 placeholder-slate-500 outline-none focus:border-indigo-500"
          />
          <button
            type="button"
            onClick={() => remove(i)}
            className="text-xs text-red-400 hover:text-red-200"
          >
            ×
          </button>
        </div>
      ))}
      <button
        type="button"
        onClick={add}
        className="rounded border border-dashed border-slate-600 px-3 py-1.5 text-xs text-slate-400 hover:border-slate-400 hover:text-slate-200"
      >
        + Add link
      </button>
    </div>
  )
}
