import CodeMirror from '@uiw/react-codemirror'
import { yaml } from '@codemirror/lang-yaml'
import { markdown } from '@codemirror/lang-markdown'
import { vscodeDark } from '@uiw/codemirror-theme-vscode'

interface Props {
  path: string
  content: string
  onChange: (value: string) => void
  onSave: () => void
  saving: boolean
  saved: boolean
}

function langExtension(path: string) {
  if (path.endsWith('.yaml') || path.endsWith('.yml')) return yaml()
  return markdown()
}

export function FileEditor({ path, content, onChange, onSave, saving, saved }: Props) {
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-slate-700 px-4 py-2">
        <span className="font-mono text-sm text-slate-400">{path}</span>
        <button
          onClick={onSave}
          disabled={saving}
          className="rounded bg-indigo-600 px-3 py-1 text-sm text-white transition-colors hover:bg-indigo-500 disabled:opacity-50"
        >
          {saving ? 'Saving…' : saved ? '✓ Saved' : 'Save'}
        </button>
      </div>
      <div className="flex-1 overflow-auto">
        <CodeMirror
          value={content}
          extensions={[langExtension(path)]}
          theme={vscodeDark}
          onChange={onChange}
          height="100%"
          style={{ height: '100%' }}
        />
      </div>
    </div>
  )
}
