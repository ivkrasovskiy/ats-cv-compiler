interface BulletListEditorProps {
  value: string[]
  onChange: (bullets: string[]) => void
  placeholder?: string
}

export function BulletListEditor({ value, onChange, placeholder }: BulletListEditorProps) {
  const update = (index: number, text: string) => {
    const next = [...value]
    next[index] = text
    onChange(next)
  }

  const remove = (index: number) => {
    onChange(value.filter((_, i) => i !== index))
  }

  const moveUp = (index: number) => {
    if (index === 0) return
    const next = [...value]
    ;[next[index - 1], next[index]] = [next[index], next[index - 1]]
    onChange(next)
  }

  const moveDown = (index: number) => {
    if (index === value.length - 1) return
    const next = [...value]
    ;[next[index], next[index + 1]] = [next[index + 1], next[index]]
    onChange(next)
  }

  const add = () => {
    onChange([...value, ''])
  }

  return (
    <div className="space-y-2">
      {value.map((bullet, i) => (
        <div key={i} className="flex items-start gap-1">
          <div className="flex flex-col gap-0.5 pt-1">
            <button
              type="button"
              onClick={() => moveUp(i)}
              disabled={i === 0}
              className="rounded px-1 text-xs text-slate-500 hover:text-slate-300 disabled:opacity-30"
              title="Move up"
            >
              ▲
            </button>
            <button
              type="button"
              onClick={() => moveDown(i)}
              disabled={i === value.length - 1}
              className="rounded px-1 text-xs text-slate-500 hover:text-slate-300 disabled:opacity-30"
              title="Move down"
            >
              ▼
            </button>
          </div>
          <textarea
            value={bullet}
            onChange={e => update(i, e.target.value)}
            placeholder={placeholder ?? 'Bullet point…'}
            rows={2}
            className="flex-1 rounded-lg border border-slate-600 bg-slate-800 px-3 py-1.5 font-mono text-sm text-slate-200 placeholder-slate-500 outline-none focus:border-indigo-500"
          />
          <button
            type="button"
            onClick={() => remove(i)}
            className="mt-1 rounded px-2 py-1 text-xs text-red-400 hover:bg-red-900 hover:text-red-200"
            title="Remove"
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
        + Add bullet
      </button>
    </div>
  )
}
