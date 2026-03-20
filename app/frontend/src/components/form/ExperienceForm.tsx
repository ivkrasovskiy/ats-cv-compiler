import { useFormData } from '../../hooks/useFormData'
import { FieldRow } from './FieldRow'
import { MonthInput } from './MonthInput'
import { TagsInput } from './TagsInput'
import { BulletListEditor } from './BulletListEditor'

interface ExperienceFields {
  company: string
  title: string
  location: string
  start_date: string
  end_date: string
  tags: string[]
  keywords: string[]
  bullets: string[]
}

interface ExperienceFormProps {
  path: string
  onSaved?: () => void
}

export function ExperienceForm({ path, onSaved }: ExperienceFormProps) {
  const { fields, loading, saving, saved, errors, setFields, handleSave } =
    useFormData<ExperienceFields>(path, onSaved)

  if (loading) return <p className="text-sm text-slate-500 p-4">Loading…</p>
  if (!fields) return <p className="text-sm text-red-400 p-4">Failed to load form.</p>

  const update = (key: keyof ExperienceFields, value: unknown) =>
    setFields(f => f ? { ...f, [key]: value } : f)

  return (
    <div className="space-y-4 p-4">
      <FieldRow label="Company" error={errors.company}>
        <input
          className="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 outline-none focus:border-indigo-500"
          value={fields.company}
          onChange={e => update('company', e.target.value)}
        />
      </FieldRow>
      <FieldRow label="Title" error={errors.title}>
        <input
          className="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 outline-none focus:border-indigo-500"
          value={fields.title}
          onChange={e => update('title', e.target.value)}
        />
      </FieldRow>
      <FieldRow label="Location">
        <input
          className="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 outline-none focus:border-indigo-500"
          value={fields.location}
          onChange={e => update('location', e.target.value)}
        />
      </FieldRow>
      <div className="grid grid-cols-2 gap-3">
        <FieldRow label="Start date" error={errors.start_date}>
          <MonthInput value={fields.start_date} onChange={v => update('start_date', v)} />
        </FieldRow>
        <FieldRow label="End date">
          <MonthInput value={fields.end_date} onChange={v => update('end_date', v)} />
        </FieldRow>
      </div>
      <FieldRow label="Tags">
        <TagsInput value={fields.tags} onChange={v => update('tags', v)} />
      </FieldRow>
      <FieldRow label="Keywords" hint="Optional — extra job-matching keywords">
        <TagsInput value={fields.keywords} onChange={v => update('keywords', v)} />
      </FieldRow>
      <FieldRow label="Bullets">
        <BulletListEditor value={fields.bullets} onChange={v => update('bullets', v)} />
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
