import React, { useState, useCallback } from 'react'
import CodeMirror from '@uiw/react-codemirror'
import { markdown } from '@codemirror/lang-markdown'
import { vscodeDark } from '@uiw/codemirror-theme-vscode'

// ── data model ────────────────────────────────────────────────────────────────

interface CvSubSection {
  title: string   // ### heading text without the ### prefix
  content: string // body lines after the heading
}

interface CvSection {
  hashes: string        // '#', '##', '###', or '' for plain text header
  title: string         // heading text without hashes
  preamble: string      // content before first ### (or entire body if no subsections)
  subsections: CvSubSection[]
}

// ── parsing ───────────────────────────────────────────────────────────────────

function parseSection(raw: string): CvSection {
  const newlineIdx = raw.indexOf('\n')
  const firstLine = newlineIdx === -1 ? raw : raw.slice(0, newlineIdx)
  const rest = newlineIdx === -1 ? '' : raw.slice(newlineIdx + 1)

  const match = firstLine.match(/^(#{1,3}) (.+)$/)
  if (!match) {
    return { hashes: '', title: firstLine, preamble: rest, subsections: [] }
  }

  const hashes = match[1]
  const title = match[2].trim()
  const body = rest.startsWith('\n') ? rest.slice(1) : rest

  // Check for ### subsections in body
  const parts = body.split(/(?:^|\n)(?=### )/)
  const hasSubsections = parts.some(p => p.startsWith('### '))

  if (hasSubsections) {
    const preamble = parts[0].startsWith('### ') ? '' : parts[0].trimEnd()
    const subParts = hasSubsections ? parts.filter(p => p.startsWith('### ')) : []
    const subsections: CvSubSection[] = subParts.map(p => {
      const nl = p.indexOf('\n')
      const subHeading = nl === -1 ? p : p.slice(0, nl)
      const subContent = nl === -1 ? '' : p.slice(nl + 1).trimEnd()
      const subMatch = subHeading.match(/^### (.+)$/)
      return { title: subMatch ? subMatch[1].trim() : subHeading, content: subContent }
    })
    return { hashes, title, preamble, subsections }
  }

  return { hashes, title, preamble: body.trimEnd(), subsections: [] }
}

function serializeSection(s: CvSection): string {
  const header = s.hashes ? `${s.hashes} ${s.title}` : s.title
  if (s.subsections.length > 0) {
    const subContent =
      (s.preamble ? s.preamble + '\n' : '') +
      s.subsections.map(sub => `### ${sub.title}\n${sub.content}`).join('\n')
    return `${header}\n${subContent}`
  }
  if (s.preamble) return `${header}\n${s.preamble}`
  return header
}

function splitSections(content: string): CvSection[] {
  return content
    .split(/\n---\n/)
    .map(s => s.replace(/^\n+/, '').replace(/\n+$/, ''))
    .filter(s => s.trim() !== '')
    .map(parseSection)
}

function joinSections(sections: CvSection[]): string {
  return sections.map(serializeSection).join('\n---\n')
}

// ── markdown tips bar ─────────────────────────────────────────────────────────

function MarkdownTips() {
  const tips: { label: string; example: string }[] = [
    { label: 'bold', example: '**text**' },
    { label: 'italic', example: '*text*' },
    { label: 'bullet', example: '– item' },
    { label: 'numbered', example: '1. item' },
    { label: 'indent bullet', example: '  – sub' },
  ]
  return (
    <div className="shrink-0 flex items-center gap-3 flex-wrap border-b border-slate-700 bg-slate-900/60 px-4 py-1.5 text-xs text-slate-500">
      <span className="text-slate-400 font-medium">Tips:</span>
      {tips.map(t => (
        <span key={t.label} title={t.label}>
          <code className="rounded bg-slate-800 px-1 py-0.5 text-slate-300">{t.example}</code>
        </span>
      ))}
      <a
        href="https://www.markdownguide.org/basic-syntax/"
        target="_blank"
        rel="noreferrer"
        className="ml-auto text-indigo-500 hover:text-indigo-400 underline"
      >
        Full guide ↗
      </a>
    </div>
  )
}

// ── subsection panel ──────────────────────────────────────────────────────────

function SubSectionPanel({
  sub,
  onChange,
}: {
  sub: CvSubSection
  onChange: (updated: CvSubSection) => void
}) {
  const [open, setOpen] = useState(true)
  const lines = sub.content.split('\n').length
  const editorHeight = `${Math.min(Math.max(lines + 2, 4), 20) * 1.55}rem`

  return (
    <div className="border-t border-slate-800">
      <div className="flex items-center gap-2 bg-slate-900/40 px-4 py-1.5">
        <button
          onClick={() => setOpen(o => !o)}
          className="shrink-0 text-xs text-slate-600 hover:text-slate-400"
        >
          {open ? '▼' : '▶'}
        </button>
        <span className="shrink-0 font-mono text-xs text-slate-600">###</span>
        <input
          value={sub.title}
          onChange={e => onChange({ ...sub, title: e.target.value })}
          className="flex-1 bg-transparent text-sm text-slate-200 outline-none placeholder:text-slate-600"
          placeholder="Subsection title"
        />
      </div>
      {open && (
        <CodeMirror
          value={sub.content}
          extensions={[markdown()]}
          theme={vscodeDark}
          onChange={v => onChange({ ...sub, content: v })}
          height={editorHeight}
        />
      )}
    </div>
  )
}

// ── section panel ─────────────────────────────────────────────────────────────

function SectionPanel({
  section,
  onChange,
}: {
  section: CvSection
  onChange: (updated: CvSection) => void
}) {
  const [open, setOpen] = useState(true)
  const preambleLines = section.preamble.split('\n').length
  const preambleHeight = `${Math.min(Math.max(preambleLines + 2, 3), 16) * 1.55}rem`

  const handleSubChange = useCallback(
    (i: number, updated: CvSubSection) => {
      onChange({
        ...section,
        subsections: section.subsections.map((s, j) => (j === i ? updated : s)),
      })
    },
    [section, onChange],
  )

  const displayHashes = section.hashes || '  '

  return (
    <div className="border-b border-slate-800">
      {/* Section header */}
      <button
        onClick={() => setOpen(o => !o)}
        className="flex w-full items-center gap-2 bg-slate-900 px-4 py-2 text-left hover:bg-slate-800/60"
      >
        <span className="shrink-0 text-xs text-slate-600">{open ? '▼' : '▶'}</span>
        <span className="shrink-0 font-mono text-xs text-slate-500">{displayHashes}</span>
        <span className="flex-1 text-sm font-medium text-slate-200 truncate">
          {section.title || <span className="text-slate-600">Untitled section</span>}
        </span>
        {section.subsections.length > 0 && (
          <span className="text-xs text-slate-600">{section.subsections.length} entries</span>
        )}
      </button>

      {open && (
        <div>
          {/* Editable section title */}
          <div className="flex items-center gap-2 border-t border-slate-800 bg-slate-900/60 px-4 py-1.5">
            <span className="shrink-0 font-mono text-xs text-slate-500">{displayHashes}</span>
            <input
              value={section.title}
              onChange={e => onChange({ ...section, title: e.target.value })}
              className="flex-1 bg-transparent text-sm font-semibold text-slate-100 outline-none placeholder:text-slate-600"
              placeholder="Section title"
            />
          </div>

          {/* Preamble content */}
          {(section.preamble || section.subsections.length === 0) && (
            <CodeMirror
              value={section.preamble}
              extensions={[markdown()]}
              theme={vscodeDark}
              onChange={v => onChange({ ...section, preamble: v })}
              height={preambleHeight}
            />
          )}

          {/* Subsections */}
          {section.subsections.map((sub, i) => (
            <SubSectionPanel
              key={i}
              sub={sub}
              onChange={updated => handleSubChange(i, updated)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

// ── main component ────────────────────────────────────────────────────────────

interface Props {
  content: string
  onChange: (value: string) => void
  onSave: () => void
  onCancel?: () => void
  saving: boolean
  saved: boolean
  extraActions?: React.ReactNode
}

export function CvSectionEditor({
  content,
  onChange,
  onSave,
  onCancel,
  saving,
  saved,
  extraActions,
}: Props) {
  const [sections, setSections] = useState<CvSection[]>(() => splitSections(content))

  const handleSectionChange = useCallback(
    (index: number, updated: CvSection) => {
      setSections(prev => {
        const next = prev.map((s, i) => (i === index ? updated : s))
        onChange(joinSections(next))
        return next
      })
    },
    [onChange],
  )

  return (
    <div className="flex h-full flex-col">
      {/* Header bar */}
      <div className="flex items-center justify-between border-b border-slate-700 px-4 py-2 shrink-0">
        <span className="text-xs text-slate-500">
          {sections.length} section{sections.length !== 1 ? 's' : ''}
          {' · '}
          <span className="text-slate-600">section names and heading levels are preserved automatically</span>
        </span>
        <div className="flex gap-2">
          {extraActions}
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

      <MarkdownTips />

      {/* Sections list */}
      <div className="flex-1 overflow-y-auto">
        {sections.map((section, i) => (
          <SectionPanel
            key={`${section.hashes}-${section.title}-${i}`}
            section={section}
            onChange={updated => handleSectionChange(i, updated)}
          />
        ))}
      </div>
    </div>
  )
}
