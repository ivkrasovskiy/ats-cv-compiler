import type { FileItem } from '../api/client'

export interface FilePair {
  base: string
  md: FileItem | null
  pdf: FileItem | null
  coverLetter: FileItem | null
}

export function groupFiles(files: FileItem[]): { pairs: FilePair[]; unpairedPdfs: FileItem[] } {
  const mdMap = new Map<string, FileItem>()
  const pdfMap = new Map<string, FileItem>()
  const coverLetterMap = new Map<string, FileItem>()

  for (const f of files) {
    if (f.name.startsWith('cover_letter_') && f.name.endsWith('.md')) {
      const clBase = f.name.replace(/^cover_letter_/, '').replace(/\.md$/, '')
      coverLetterMap.set(clBase, f)
    } else if (f.name.endsWith('.md')) {
      mdMap.set(f.name.replace(/\.md$/, ''), f)
    } else if (f.name.endsWith('.pdf')) {
      pdfMap.set(f.name.replace(/\.pdf$/, ''), f)
    }
  }

  const allBases = new Set([...mdMap.keys(), ...pdfMap.keys()])
  const pairs: FilePair[] = []
  const unpairedPdfs: FileItem[] = []

  for (const base of allBases) {
    const md = mdMap.get(base) ?? null
    const pdf = pdfMap.get(base) ?? null
    const cvJobBase = base.startsWith('cv_') ? base.replace(/^cv_/, '') : null
    const coverLetter = cvJobBase ? (coverLetterMap.get(cvJobBase) ?? null) : null
    if (md || pdf) {
      if (!md && pdf) {
        unpairedPdfs.push(pdf)
      } else {
        pairs.push({ base, md, pdf, coverLetter })
      }
    }
  }

  pairs.sort((a, b) => a.base.localeCompare(b.base))
  return { pairs, unpairedPdfs }
}
