import { useEffect, useRef, useState } from 'react'
import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import { WebLinksAddon } from '@xterm/addon-web-links'

export type TerminalStatus = 'idle' | 'connecting' | 'connected' | 'disconnected' | 'error'

interface UseAgentTerminalResult {
  termRef: React.RefObject<HTMLDivElement | null>
  status: TerminalStatus
  start: (cli?: string) => void
  stop: () => void
}

export function useAgentTerminal(): UseAgentTerminalResult {
  const termRef = useRef<HTMLDivElement | null>(null)
  const terminalRef = useRef<Terminal | null>(null)
  const fitAddonRef = useRef<FitAddon | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const [status, setStatus] = useState<TerminalStatus>('idle')

  function stop() {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setStatus('idle')
  }

  function start(cli = 'claude') {
    if (!termRef.current) return
    setStatus('connecting')

    // Create terminal if not exists
    if (!terminalRef.current) {
      const terminal = new Terminal({
        theme: {
          background: '#0f172a',
          foreground: '#e2e8f0',
          cursor: '#818cf8',
        },
        fontFamily: 'Menlo, Monaco, "Courier New", monospace',
        fontSize: 13,
        cursorBlink: true,
      })
      const fitAddon = new FitAddon()
      const webLinksAddon = new WebLinksAddon()
      terminal.loadAddon(fitAddon)
      terminal.loadAddon(webLinksAddon)
      terminal.open(termRef.current)
      fitAddon.fit()
      terminalRef.current = terminal
      fitAddonRef.current = fitAddon
    }

    const terminal = terminalRef.current

    const wsUrl = `ws://localhost:8000/ws/agent?cli=${encodeURIComponent(cli)}`
    const ws = new WebSocket(wsUrl)
    ws.binaryType = 'arraybuffer'
    wsRef.current = ws

    ws.onopen = () => {
      setStatus('connected')
      // Send initial size
      const { rows, cols } = terminal
      ws.send(JSON.stringify({ type: 'resize', rows, cols }))
    }

    ws.onmessage = (event) => {
      if (event.data instanceof ArrayBuffer) {
        terminal.write(new Uint8Array(event.data))
      } else {
        terminal.write(event.data)
      }
    }

    ws.onerror = () => {
      setStatus('error')
    }

    ws.onclose = () => {
      setStatus((prev) => (prev === 'connecting' ? 'error' : 'disconnected'))
    }

    // Forward keystrokes
    terminal.onData((data) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(new TextEncoder().encode(data))
      }
    })
  }

  // ResizeObserver for terminal fit
  useEffect(() => {
    if (!termRef.current) return
    const observer = new ResizeObserver(() => {
      if (fitAddonRef.current && terminalRef.current && wsRef.current?.readyState === WebSocket.OPEN) {
        fitAddonRef.current.fit()
        const { rows, cols } = terminalRef.current
        wsRef.current.send(JSON.stringify({ type: 'resize', rows, cols }))
      }
    })
    observer.observe(termRef.current)
    return () => observer.disconnect()
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stop()
      terminalRef.current?.dispose()
      terminalRef.current = null
    }
  }, [])

  return { termRef, status, start, stop }
}
