import { useFormData } from '../../hooks/useFormData'
import { FieldRow } from './FieldRow'
import { MonthInput } from './MonthInput'
import { TagsInput } from './TagsInput'

interface EducationEntry {
  institution: string
  degree: string
  location: string
  start_date: string
  end_date: string
}

interface EducationFields {
  entries: EducationEntry[]
  languages: string[]
}

interface EducationFormProps {
  path: string
  onSaved?: () => void
}

export function EducationForm({ path, onSaved }: EducationFormProps) {
  const { fields, loading, saving, saved, errors, setFields, handleSave } =
    useFormData<EducationFields>(path, onSaved)

  if (loading) return <p className="text-sm text-slate-500 p-4">Loading…</p>
  if (!fields) return <p className="text-sm text-red-400 p-4">Failed to load form.</p>

  const entries = fields.entries ?? []
  const languages = fields.languages ?? []

  const updateEntry = (index: number, key: keyof EducationEntry, value: string) => {
    setFields(f => f ? { ...f, entries: f.entries.map((e, i) => i === index ? { ...e, [key]: value } : e) } : f)
  }

  const removeEntry = (index: number) => {
    setFields(f => f ? { ...f, entries: f.entries.filter((_, i) => i !== index) } : f)
  }

  const addEntry = () => {
    setFields(f => f ? { ...f, entries: [...f.entries, { institution: '', degree: '', location: '', start_date: '', end_date: '' }] } : f)
  }

  return (
    <div className="space-y-4 p-4">
      {errors.entries && <p className="text-xs text-red-400">{errors.entries}</p>}
      {entries.map((entry, i) => (
        <div key={i} className="rounded-lg border border-slate-700 bg-slate-900 p-3 space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-xs font-medium text-slate-400">Entry {i + 1}</span>
            <button type="button" onClick={() => removeEntry(i)} className="text-xs text-red-400 hover:text-red-200">Remove</button>
          </div>
          <FieldRow label="Institution">
            <input
              className="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 outline-none focus:border-indigo-500"
              value={entry.institution}
              onChange={e => updateEntry(i, 'institution', e.target.value)}
            />
          </FieldRow>
          <FieldRow label="Degree">
            <input
              className="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 outline-none focus:border-indigo-500"
              value={entry.degree}
              onChange={e => updateEntry(i, 'degree', e.target.value)}
            />
          </FieldRow>
          <FieldRow label="Location">
            <input
              className="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 outline-none focus:border-indigo-500"
              value={entry.location}
              onChange={e => updateEntry(i, 'location', e.target.value)}
            />
          </FieldRow>
          <div className="grid grid-cols-2 gap-3">
            <FieldRow label="Start date">
              <MonthInput value={entry.start_date} onChange={v => updateEntry(i, 'start_date', v)} />
            </FieldRow>
            <FieldRow label="End date">
              <MonthInput value={entry.end_date} onChange={v => updateEntry(i, 'end_date', v)} />
            </FieldRow>
          </div>
        </div>
      ))}
      <button
        type="button"
        onClick={addEntry}
        className="rounded border border-dashed border-slate-600 px-3 py-1.5 text-xs text-slate-400 hover:border-slate-400 hover:text-slate-200"
      >
        + Add entry
      </button>
      <FieldRow label="Languages">
        <TagsInput
          value={languages}
          onChange={v => setFields(f => f ? { ...f, languages: v } : f)}
          placeholder="e.g. English - Native"
        />
      </FieldRow>
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
