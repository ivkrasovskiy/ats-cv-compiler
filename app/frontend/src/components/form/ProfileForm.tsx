import { useFormData } from '../../hooks/useFormData'
import { FieldRow } from './FieldRow'
import { LinkList } from './LinkList'

interface ProfileFields {
  name: string
  headline: string
  email: string
  location: string
  about_me: string
  links: { label: string; url: string }[]
}

interface ProfileFormProps {
  path: string
  onSaved?: () => void
}

export function ProfileForm({ path, onSaved }: ProfileFormProps) {
  const { fields, loading, saving, saved, errors, setFields, handleSave } =
    useFormData<ProfileFields>(path, onSaved)

  if (loading) return <p className="text-sm text-slate-500 p-4">Loading…</p>
  if (!fields) return <p className="text-sm text-red-400 p-4">Failed to load form.</p>

  const update = (key: keyof ProfileFields, value: unknown) =>
    setFields(f => f ? { ...f, [key]: value } : f)

  return (
    <div className="space-y-4 p-4">
      <FieldRow label="Name" error={errors.name}>
        <input
          className="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 outline-none focus:border-indigo-500"
          value={fields.name}
          onChange={e => update('name', e.target.value)}
        />
      </FieldRow>
      <FieldRow label="Headline" error={errors.headline}>
        <input
          className="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 outline-none focus:border-indigo-500"
          value={fields.headline}
          onChange={e => update('headline', e.target.value)}
        />
      </FieldRow>
      <FieldRow label="Email" error={errors.email}>
        <input
          type="email"
          className="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 outline-none focus:border-indigo-500"
          value={fields.email}
          onChange={e => update('email', e.target.value)}
        />
      </FieldRow>
      <FieldRow label="Location" error={errors.location}>
        <input
          className="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 outline-none focus:border-indigo-500"
          value={fields.location}
          onChange={e => update('location', e.target.value)}
        />
      </FieldRow>
      <FieldRow label="About me" error={errors.about_me}>
        <textarea
          rows={4}
          className="w-full rounded-lg border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 outline-none focus:border-indigo-500"
          value={fields.about_me}
          onChange={e => update('about_me', e.target.value)}
        />
      </FieldRow>
      <FieldRow label="Links" error={errors.links}>
        <LinkList value={fields.links} onChange={v => update('links', v)} />
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
