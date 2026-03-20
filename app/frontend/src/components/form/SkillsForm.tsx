import { useFormData } from '../../hooks/useFormData'
import { FieldRow } from './FieldRow'
import { TagsInput } from './TagsInput'

interface SkillCategory {
  name: string
  items: string[]
}

interface SkillsFields {
  categories: SkillCategory[]
}

interface SkillsFormProps {
  path: string
  onSaved?: () => void
}

export function SkillsForm({ path, onSaved }: SkillsFormProps) {
  const { fields, loading, saving, saved, errors, setFields, handleSave } =
    useFormData<SkillsFields>(path, onSaved)

  if (loading) return <p className="text-sm text-slate-500 p-4">Loading…</p>
  if (!fields) return <p className="text-sm text-red-400 p-4">Failed to load form.</p>

  const categories = fields.categories ?? []

  const updateCategory = (index: number, key: keyof SkillCategory, value: unknown) => {
    setFields(f => f ? { ...f, categories: f.categories.map((c, i) => i === index ? { ...c, [key]: value } : c) } : f)
  }

  const removeCategory = (index: number) => {
    setFields(f => f ? { ...f, categories: f.categories.filter((_, i) => i !== index) } : f)
  }

  const addCategory = () => {
    setFields(f => f ? { ...f, categories: [...f.categories, { name: '', items: [] }] } : f)
  }

  return (
    <div className="space-y-4 p-4">
      {errors.categories && <p className="text-xs text-red-400">{errors.categories}</p>}
      {categories.map((cat, i) => (
        <div key={i} className="rounded-lg border border-slate-700 bg-slate-900 p-3 space-y-3">
          <div className="flex items-center gap-2">
            <input
              className="flex-1 rounded-lg border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm font-medium text-slate-200 outline-none focus:border-indigo-500"
              placeholder="Category name"
              value={cat.name}
              onChange={e => updateCategory(i, 'name', e.target.value)}
            />
            <button
              type="button"
              onClick={() => removeCategory(i)}
              className="text-xs text-red-400 hover:text-red-200"
            >
              Remove
            </button>
          </div>
          <FieldRow label="Skills">
            <TagsInput
              value={cat.items}
              onChange={v => updateCategory(i, 'items', v)}
              placeholder="Add skill, press Enter"
            />
          </FieldRow>
        </div>
      ))}
      <button
        type="button"
        onClick={addCategory}
        className="rounded border border-dashed border-slate-600 px-3 py-1.5 text-xs text-slate-400 hover:border-slate-400 hover:text-slate-200"
      >
        + Add category
      </button>
      <div className="flex gap-2 pt-2">
        <button
          onClick={() => void handleSave()}
          disabled={saving}
          className="rounded-lg bg-indigo-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
        >
          {saving ? 'Saving…' : saved ? '✓ Saved' : 'Save'}
        </button>
      </div>
    </div>
  )
}
