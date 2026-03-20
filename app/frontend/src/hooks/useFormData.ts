import { useState, useEffect } from 'react'
import { getDataFileForm, putDataFileForm } from '../api/client'

interface UseFormDataResult<T> {
  fields: T | null
  loading: boolean
  saving: boolean
  saved: boolean
  errors: Record<string, string>
  setFields: React.Dispatch<React.SetStateAction<T | null>>
  handleSave: () => Promise<void>
}

export function useFormData<T>(path: string, onSaved?: () => void): UseFormDataResult<T> {
  const [fields, setFields] = useState<T | null>(null)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    setLoading(true)
    setFields(null)
    getDataFileForm(path)
      .then(res => setFields(res.fields as T))
      .finally(() => setLoading(false))
  }, [path])

  const handleSave = async () => {
    if (!fields) return
    setSaving(true)
    setErrors({})
    try {
      await putDataFileForm(path, fields as Record<string, unknown>)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
      onSaved?.()
    } catch (err: unknown) {
      if (err instanceof Error) {
        try {
          const data = JSON.parse(err.message.replace(/^\d+ /, ''))
          if (typeof data === 'object' && data !== null) {
            setErrors(data as Record<string, string>)
          }
        } catch { /* ignore */ }
      }
    } finally {
      setSaving(false)
    }
  }

  return { fields, loading, saving, saved, errors, setFields, handleSave }
}
