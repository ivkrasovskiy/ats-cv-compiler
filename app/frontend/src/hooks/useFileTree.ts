import { useQuery } from '@tanstack/react-query'
import { listDataFiles, listJobFiles, type FileItem } from '../api/client'

export function useDataFileTree() {
  return useQuery<FileItem[]>({
    queryKey: ['files', 'data'],
    queryFn: listDataFiles,
  })
}

export function useJobFileTree() {
  return useQuery<FileItem[]>({
    queryKey: ['files', 'jobs'],
    queryFn: listJobFiles,
  })
}
