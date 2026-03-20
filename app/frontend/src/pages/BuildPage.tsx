import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getConfig,
  putConfig,
  listPrompts,
  getPrompt,
  putPrompt,
} from '../api/client'
import type { ConfigData } from '../api/client'
import { Tooltip } from '../components/Tooltip'
import { FileEditor } from '../components/FileEditor'
import { ConfirmDialog } from '../components/ConfirmDialog'

const BASIC_LABELS: Record<string, { label: string; tip: string; type: 'text' | 'boolean' | 'number' }> = {
  CV_AGENT_CHAIN_ENABLED: { label: 'Agent Chain', tip: 'Enable the multi-step agent pipeline for higher-quality bullet rewriting.', type: 'boolean' },
  CV_AGENT_MAX_BULLET_CHARS: { label: 'Max Bullet Length', tip: 'Maximum characters per bullet point (default: 200).', type: 'number' },
  CV_AGENT_MAX_SUMMARY_CHARS: { label: 'Max Summary Length', tip: 'Maximum characters for the professional summary section (default: 1500).', type: 'number' },
  CV_AGENT_KEYWORD_COVERAGE_MIN: { label: 'Keyword Coverage', tip: 'Minimum fraction of job keywords that must appear in the CV (0–1, default: 0.5).', type: 'number' },
}

const ADV_LLM_LABELS: Record<string, { label: string; tip: string }> = {
  CV_LLM_BASE_URL: { label: 'Base URL', tip: 'OpenAI-compatible API base URL.' },
  CV_LLM_API_KEY: { label: 'API Key', tip: 'Your LLM provider API key.' },
  CV_LLM_MODEL: { label: 'Model name', tip: 'Model identifier used by the custom LLM (e.g. gpt-4o, llama-3).' },
  CV_LLM_TIMEOUT_SECONDS: { label: 'Timeout (s)', tip: 'Request timeout in seconds.' },
}

const AI_PROVIDER_OPTIONS = [
  { value: 'gemini', label: 'Gemini CLI', desc: 'Free; requires gemini CLI installed' },
  { value: 'claude', label: 'Claude CLI', desc: 'Requires Claude Pro subscription' },
  { value: 'custom', label: 'Custom endpoint', desc: 'OpenAI-compatible API' },
] as const
type AiProvider = typeof AI_PROVIDER_OPTIONS[number]['value']

const ADV_TIMEOUT_LABELS: Record<string, { label: string; tip: string }> = {
  CV_AGENT_TIMEOUT_JOB_ANALYSIS: { label: 'Job Analysis Timeout (s)', tip: 'Timeout for the job analysis step.' },
  CV_AGENT_TIMEOUT_EXPERIENCE: { label: 'Experience Timeout (s)', tip: 'Timeout for experience bullet generation.' },
  CV_AGENT_TIMEOUT_SKILLS: { label: 'Skills Timeout (s)', tip: 'Timeout for skills processing.' },
  CV_AGENT_TIMEOUT_BULLET_POLISH: { label: 'Bullet Polish Timeout (s)', tip: 'Timeout for bullet polishing step.' },
  CV_AGENT_TIMEOUT_SUMMARY: { label: 'Summary Timeout (s)', tip: 'Timeout for summary generation.' },
}

function ConfigField({
  label,
  tip,
  type,
  value,
  onChange,
}: {
  label: string
  tip: string
  type: 'text' | 'boolean' | 'number'
  value: string
  onChange: (v: string) => void
}) {
  return (
    <div className="flex items-center justify-between gap-4 py-2">
      <Tooltip text={tip}>
        <label className="text-sm text-slate-300">{label}</label>
      </Tooltip>
      {type === 'boolean' ? (
        <button
          onClick={() => onChange(value.toLowerCase() === 'true' ? 'false' : 'true')}
          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
            value.toLowerCase() === 'true' ? 'bg-indigo-600' : 'bg-slate-600'
          }`}
        >
          <span
            className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
              value.toLowerCase() === 'true' ? 'translate-x-6' : 'translate-x-1'
            }`}
          />
        </button>
      ) : (
        <input
          type={type === 'number' ? 'text' : 'text'}
          value={value}
          onChange={e => onChange(e.target.value)}
          className="w-48 rounded-lg border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm text-slate-200 outline-none focus:border-indigo-500"
        />
      )}
    </div>
  )
}

export function BuildPage() {
  const qc = useQueryClient()
  const configQ = useQuery({ queryKey: ['config'], queryFn: getConfig })
  const promptsQ = useQuery({ queryKey: ['prompts'], queryFn: listPrompts })

  const [localConfig, setLocalConfig] = useState<ConfigData | null>(null)
  const [saveDone, setSaveDone] = useState(false)
  const [editingPrompt, setEditingPrompt] = useState<string | null>(null)
  const [promptDraft, setPromptDraft] = useState('')
  const [promptSaved, setPromptSaved] = useState(false)
  const [discardPromptDialog, setDiscardPromptDialog] = useState(false)

  useEffect(() => {
    if (configQ.data && !localConfig) {
      setLocalConfig(structuredClone(configQ.data))
    }
  }, [configQ.data, localConfig])

  const saveMut = useMutation({
    mutationFn: () => putConfig(localConfig!),
    onSuccess: () => {
      setSaveDone(true)
      void qc.invalidateQueries({ queryKey: ['config'] })
      setTimeout(() => setSaveDone(false), 2000)
    },
  })

  const promptQ = useQuery({
    queryKey: ['prompt', editingPrompt],
    queryFn: () => getPrompt(editingPrompt!),
    enabled: editingPrompt !== null,
    staleTime: Infinity,
  })

  const savePromptMut = useMutation({
    mutationFn: () => putPrompt(editingPrompt!, promptDraft),
    onSuccess: () => {
      setPromptSaved(true)
      setTimeout(() => setPromptSaved(false), 2000)
    },
  })

  if (promptQ.data && promptDraft === '' && promptQ.data.content) {
    setPromptDraft(promptQ.data.content)
  }

  const setBasic = (key: string, val: string) => {
    if (!localConfig) return
    setLocalConfig({ ...localConfig, basic: { ...localConfig.basic, [key]: val } })
    setSaveDone(false)
  }

  const setAdvLlm = (key: string, val: string) => {
    if (!localConfig) return
    setLocalConfig({ ...localConfig, advanced_llm: { ...localConfig.advanced_llm, [key]: val } })
  }

  const setAdvTimeout = (key: string, val: string) => {
    if (!localConfig) return
    setLocalConfig({ ...localConfig, advanced_timeouts: { ...localConfig.advanced_timeouts, [key]: val } })
  }

  const handleCancelPrompt = () => {
    const isDirty = promptDraft !== '' && promptDraft !== (promptQ.data?.content ?? '')
    if (isDirty) {
      setDiscardPromptDialog(true)
    } else {
      setEditingPrompt(null)
      setPromptDraft('')
    }
  }

  if (configQ.isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-slate-100">Gen Config</h1>
          <p className="mt-1 text-sm text-slate-400">Configure how CVs are generated</p>
        </div>
        <p className="text-sm text-slate-500">Loading…</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-100">Gen Config</h1>
        <p className="mt-1 text-sm text-slate-400">Configure how CVs are generated</p>
      </div>

      {/* Basic Settings */}
      <section className="rounded-xl border border-slate-700 bg-slate-900 p-5">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-400">
          Content Quality
        </h2>
        {localConfig && (
          <div className="divide-y divide-slate-800">
            {/* AI Provider selector */}
            <div className="py-3">
              <Tooltip text="Which AI provider is used for PDF parsing and bullet generation.">
                <label className="text-sm text-slate-300">AI Provider</label>
              </Tooltip>
              <div className="mt-2 space-y-2">
                {AI_PROVIDER_OPTIONS.map(opt => {
                  const current = (localConfig.basic['CV_AI_PROVIDER'] ?? 'gemini') as AiProvider
                  return (
                    <label key={opt.value} className="flex cursor-pointer items-start gap-2">
                      <input
                        type="radio"
                        name="ai-provider"
                        value={opt.value}
                        checked={current === opt.value}
                        onChange={() => setBasic('CV_AI_PROVIDER', opt.value)}
                        className="mt-0.5 accent-indigo-500"
                      />
                      <span className="text-sm text-slate-300">
                        <strong>{opt.label}</strong>
                        <span className="ml-2 text-slate-500">— {opt.desc}</span>
                      </span>
                    </label>
                  )
                })}
              </div>
              {/* Inline Custom endpoint fields */}
              {(localConfig.basic['CV_AI_PROVIDER'] ?? 'gemini') === 'custom' && (
                <div className="mt-3 space-y-2 rounded-lg border border-slate-700 bg-slate-800/50 p-3">
                  {(['CV_LLM_BASE_URL', 'CV_LLM_API_KEY', 'CV_LLM_MODEL'] as const).map(key => (
                    <div key={key} className="flex items-center justify-between gap-4">
                      <label className="text-xs text-slate-400">{ADV_LLM_LABELS[key].label}</label>
                      <input
                        type="text"
                        value={localConfig.advanced_llm[key] ?? ''}
                        onChange={e => setAdvLlm(key, e.target.value)}
                        placeholder={ADV_LLM_LABELS[key].tip}
                        className="w-56 rounded border border-slate-600 bg-slate-800 px-2 py-1 text-xs text-slate-200 outline-none focus:border-indigo-500"
                      />
                    </div>
                  ))}
                </div>
              )}
            </div>
            {Object.entries(BASIC_LABELS).map(([key, meta]) => (
              <ConfigField
                key={key}
                label={meta.label}
                tip={meta.tip}
                type={meta.type}
                value={localConfig.basic[key] ?? ''}
                onChange={val => setBasic(key, val)}
              />
            ))}
          </div>
        )}
        <div className="mt-4 flex items-center gap-3">
          <button
            onClick={() => saveMut.mutate()}
            disabled={saveMut.isPending || !localConfig}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
          >
            {saveMut.isPending ? 'Saving…' : 'Save Settings'}
          </button>
          {saveDone && <span className="text-sm text-green-400">✓ Saved</span>}
        </div>
      </section>

      {/* Advanced LLM */}
      <details className="rounded-xl border border-slate-700 bg-slate-900">
        <summary className="cursor-pointer px-5 py-3 text-sm font-semibold uppercase tracking-wide text-slate-400 hover:text-slate-300">
          Advanced – Custom Endpoint Settings
        </summary>
        <div className="px-5 pb-5">
          <p className="mb-4 text-xs text-slate-400">
            Additional settings for the custom OpenAI-compatible endpoint (e.g. LM Studio, Ollama). Only used when <strong>AI Provider</strong> is set to Custom.
          </p>
          <div className="divide-y divide-slate-800">
            {localConfig && Object.entries(ADV_LLM_LABELS).map(([key, meta]) => (
              <ConfigField
                key={key}
                label={meta.label}
                tip={meta.tip}
                type="text"
                value={localConfig.advanced_llm[key] ?? ''}
                onChange={val => setAdvLlm(key, val)}
              />
            ))}
          </div>
        </div>
      </details>

      {/* Advanced Timeouts */}
      <details className="rounded-xl border border-slate-700 bg-slate-900">
        <summary className="cursor-pointer px-5 py-3 text-sm font-semibold uppercase tracking-wide text-slate-400 hover:text-slate-300">
          Advanced – Agent Timeouts
        </summary>
        <div className="px-5 pb-5 divide-y divide-slate-800">
          {localConfig && Object.entries(ADV_TIMEOUT_LABELS).map(([key, meta]) => (
            <ConfigField
              key={key}
              label={meta.label}
              tip={meta.tip}
              type="text"
              value={localConfig.advanced_timeouts[key] ?? ''}
              onChange={val => setAdvTimeout(key, val)}
            />
          ))}
        </div>
      </details>

      {/* Prompts */}
      <details className="rounded-xl border border-slate-700 bg-slate-900">
        <summary className="cursor-pointer px-5 py-3 text-sm font-semibold uppercase tracking-wide text-slate-400 hover:text-slate-300">
          Prompts
        </summary>
        <div className="px-5 pb-5 space-y-3">
          <div className="rounded-lg border border-yellow-700 bg-yellow-950/30 px-3 py-2 text-xs text-yellow-300">
            ⚠️ Editing prompts affects AI output quality. Changes apply to the next build.
          </div>
          {promptsQ.isLoading && <p className="text-sm text-slate-500">Loading…</p>}
          {promptsQ.data && (
            <div className="space-y-2">
              {promptsQ.data.map(f => (
                <div key={f.path} className="flex items-center justify-between rounded-lg border border-slate-700 bg-slate-800 px-3 py-2">
                  <span className="font-mono text-xs text-slate-300">{f.name}</span>
                  <button
                    onClick={() => { setEditingPrompt(f.path); setPromptDraft('') }}
                    className="rounded bg-slate-700 px-3 py-1 text-xs text-slate-200 hover:bg-slate-600"
                  >
                    Edit
                  </button>
                </div>
              ))}
            </div>
          )}
          {editingPrompt && promptQ.data && (
            <div className="mt-3 overflow-hidden rounded-xl border border-slate-700" style={{ height: '400px' }}>
              <FileEditor
                path={editingPrompt}
                content={promptDraft || promptQ.data.content}
                onChange={v => { setPromptDraft(v); setPromptSaved(false) }}
                onSave={() => savePromptMut.mutate()}
                onCancel={handleCancelPrompt}
                saving={savePromptMut.isPending}
                saved={promptSaved}
              />
            </div>
          )}
        </div>
      </details>

      {discardPromptDialog && (
        <ConfirmDialog
          title="Discard prompt changes?"
          message="Your unsaved prompt edits will be lost."
          confirmLabel="Discard"
          cancelLabel="Keep editing"
          onConfirm={() => {
            setDiscardPromptDialog(false)
            setEditingPrompt(null)
            setPromptDraft('')
          }}
          onCancel={() => setDiscardPromptDialog(false)}
        />
      )}
    </div>
  )
}
