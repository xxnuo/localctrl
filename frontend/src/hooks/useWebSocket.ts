import { useRef, useEffect, useCallback, useState } from 'react'

type WSStatus = 'connecting' | 'connected' | 'disconnected'

interface UseWebSocketOptions {
  url: string
  token: string | null
  onMessage?: (data: MessageEvent) => void
  onOpen?: () => void
  onClose?: () => void
  reconnect?: boolean
}

export function useWebSocket({
  url,
  token,
  onMessage,
  onOpen,
  onClose,
  reconnect = true,
}: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>()
  const [status, setStatus] = useState<WSStatus>('disconnected')
  const [latency, setLatency] = useState(0)
  const pingTimer = useRef<ReturnType<typeof setInterval>>()

  const connect = useCallback(() => {
    if (!token) return
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const fullUrl = `${protocol}//${location.host}${url}?token=${token}`
    const ws = new WebSocket(fullUrl)
    ws.binaryType = 'arraybuffer'
    wsRef.current = ws
    setStatus('connecting')

    ws.onopen = () => {
      setStatus('connected')
      onOpen?.()
      pingTimer.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          const now = Date.now()
          ws.send(JSON.stringify({ type: 'ping', timestamp: now }))
        }
      }, 5000)
    }

    ws.onmessage = (ev) => {
      if (typeof ev.data === 'string') {
        try {
          const msg = JSON.parse(ev.data)
          if (msg.type === 'pong') {
            setLatency(Date.now() - msg.timestamp)
            return
          }
        } catch {}
      }
      onMessage?.(ev)
    }

    ws.onclose = () => {
      setStatus('disconnected')
      clearInterval(pingTimer.current)
      onClose?.()
      if (reconnect) {
        reconnectTimer.current = setTimeout(connect, 3000)
      }
    }

    ws.onerror = () => {
      ws.close()
    }
  }, [url, token, onMessage, onOpen, onClose, reconnect])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnectTimer.current)
      clearInterval(pingTimer.current)
      wsRef.current?.close()
    }
  }, [connect])

  const send = useCallback((data: string | ArrayBuffer) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(data)
    }
  }, [])

  const sendJSON = useCallback((obj: object) => {
    send(JSON.stringify(obj))
  }, [send])

  return { ws: wsRef, status, latency, send, sendJSON }
}
