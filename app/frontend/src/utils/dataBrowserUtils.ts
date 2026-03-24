import type { FileItem } from '../api/client'

const FORM_SUPPORTED_TYPES = new Set(['profile', 'skills', 'education', 'experience', 'project'])

type EditMode = 'form' | 'blocks' | 'raw'

export function inferFileType(path: string): string | null {
  if (path === 'profile.md') return 'profile'
  if (path === 'skills.md') return 'skills'
  if (path === 'education.md') return 'education'
  if (path.startsWith('experience/') && path.endsWith('.md')) return 'experience'
  if (path.startsWith('projects/') && path.endsWith('.md')) return 'project'
  return null
}

export function defaultMode(path: string): EditMode {
  const ft = inferFileType(path)
  if (ft !== null && FORM_SUPPORTED_TYPES.has(ft)) return 'form'
  if (path.endsWith('.md')) return 'blocks'
  return 'raw'
}

export function stripPrefix(name: string): string {
  return name
    .replace(/^llm_exp_/, '')
    .replace(/^user_exp_/, '')
    .replace(/^proj_/, '')
    .replace(/\.md$/, '')
}

export function groupByCompany(files: FileItem[]): { company: string; files: FileItem[] }[] {
  const map = new Map<string, FileItem[]>()
  for (const f of files) {
    const key = f.company ?? ''
    if (!map.has(key)) map.set(key, [])
    map.get(key)!.push(f)
  }
  return [...map.entries()]
    .sort(([a], [b]) => {
      if (a === '' && b !== '') return 1
      if (a !== '' && b === '') return -1
      return a.localeCompare(b)
    })
    .map(([company, files]) => ({ company, files }))
}
