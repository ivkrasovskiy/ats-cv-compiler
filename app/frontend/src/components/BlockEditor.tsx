import { useState, useCallback } from 'react'
import CodeMirror from '@uiw/react-codemirror'
import { yaml } from '@codemirror/lang-yaml'
import { markdown } from '@codemirror/lang-markdown'
import { vscodeDark } from '@uiw/codemirror-theme-vscode'

function splitFrontmatter(content: string): { fm: string; body: string } {
  if (!content.startsWith('---\n') && content !== '---') {
    return { fm: '', body: content }
  }
  const rest = content.slice(4)
  const closeMatch = rest.match(/^---\r?\n?/m)
  if (!closeMatch || closeMatch.index === undefined) {
    return { fm: '', body: content }
  }
  const fm = rest.slice(0, closeMatch.index)
  const body = rest.slice(closeMatch.index + closeMatch[0].length)
  return { fm, body }
}

function joinFrontmatter(fm: string, body: string): string {
  const fmTrimmed = fm.trimEnd()
  if (!fmTrimmed) return body
  return `---\n${fmTrimmed}\n---\n${body}`
}

interface Props {
  content: string
  onChange: (value: string) => void
  onSave: () => void
  onCancel?: () => void
  saving: boolean
  saved: boolean
}

export function BlockEditor({ content, onChange, onSave, onCancel, saving, saved }: Props) {
  const { fm: initFm, body: initBody } = splitFrontmatter(content)
  const [fm, setFm] = useState(initFm)
  const [body, setBody] = useState(initBody)

  const handleFmChange = useCallback(
    (value: string) => {
      setFm(value)
      onChange(joinFrontmatter(value, body))
    },
    [body, onChange],
  )

  const handleBodyChange = useCallback(
    (value: string) => {
      setBody(value)
      onChange(joinFrontmatter(fm, value))
    },
    [fm, onChange],
  )

  return (
    <div className="flex h-full flex-col">
      {/* Frontmatter block */}
      <div className="flex items-center justify-between border-b border-slate-700 bg-slate-900/60 px-4 py-1.5 shrink-0">
        <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Frontmatter — YAML
        </span>
        <div className="flex gap-2">
          {onCancel && (
            <button
              onClick={onCancel}
              className="rounded bg-slate-700 px-3 py-1 text-sm text-slate-300 hover:bg-slate-600"
            >
              Cancel
            </button>
          )}
          <button
            onClick={onSave}
            disabled={saving}
            className="rounded bg-indigo-600 px-3 py-1 text-sm text-white transition-colors hover:bg-indigo-500 disabled:opacity-50"
          >
            {saving ? 'Saving…' : saved ? '✓ Saved' : 'Save'}
          </button>
        </div>
      </div>
      <div style={{ height: '45%' }} className="overflow-auto border-b border-slate-700">
        <CodeMirror
          value={fm}
          extensions={[yaml()]}
          theme={vscodeDark}
          onChange={handleFmChange}
          height="100%"
          style={{ height: '100%' }}
        />
      </div>

      {/* Body block */}
      <div className="border-b border-slate-700 bg-slate-900/60 px-4 py-1.5 shrink-0">
        <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Markdown Body
        </span>
      </div>
      <div className="flex-1 overflow-auto">
        <CodeMirror
          value={body}
          extensions={[markdown()]}
          theme={vscodeDark}
          onChange={handleBodyChange}
          height="100%"
          style={{ height: '100%' }}
        />
      </div>
    </div>
  )
}
