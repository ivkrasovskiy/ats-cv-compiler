import { useEffect } from 'react'
import { buildStreamUrl } from '../api/client'
import { useBuildStore } from '../store/buildStore'

export function useBuildStream(jobId: string | null) {
  const appendLine = useBuildStore(s => s.appendLine)
  const setStatus = useBuildStore(s => s.setStatus)

  useEffect(() => {
    if (!jobId) return

    const es = new EventSource(buildStreamUrl(jobId))

    es.onmessage = e => {
      const data: string = e.data as string
      if (data === '[DONE]') {
        es.close()
        // Final status is already set by the store via polling or here
        setStatus('done')
      } else {
        appendLine(data)
      }
    }

    es.onerror = () => {
      es.close()
      setStatus('error')
    }

    return () => {
      es.close()
    }
  }, [jobId, appendLine, setStatus])
}
