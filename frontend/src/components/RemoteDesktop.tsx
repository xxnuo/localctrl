import { useRef, useEffect, useState, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../hooks/useAuth'
import { useWebSocket } from '../hooks/useWebSocket'
import { Maximize, Settings2, Monitor, Keyboard } from 'lucide-react'
import type { ScreenInfo, MonitorList, ControlGrant } from '../types/protocol'

interface Props {
  onStatsUpdate: (stats: { bandwidth: number; latency: number; fps: number }) => void
}

export default function RemoteDesktop({ onStatsUpdate }: Props) {
  const { t } = useTranslation()
  const { token } = useAuth()
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [screenInfo, setScreenInfo] = useState<ScreenInfo | null>(null)
  const [monitors, setMonitors] = useState<MonitorList['monitors']>([])
  const [isController, setIsController] = useState(false)
  const [showToolbar, setShowToolbar] = useState(true)
  const [quality, setQuality] = useState(60)
  const [fps, setFps] = useState(20)
  const frameCount = useRef(0)
  const bytesReceived = useRef(0)
  const lastStatsTime = useRef(Date.now())

  const handleMessage = useCallback((ev: MessageEvent) => {
    if (typeof ev.data === 'string') {
      try {
        const msg = JSON.parse(ev.data)
        switch (msg.type) {
          case 'screen_info':
            setScreenInfo(msg)
            break
          case 'monitor_list':
            setMonitors(msg.monitors)
            break
          case 'control_grant':
            setIsController(msg.granted)
            break
        }
      } catch {}
    } else if (ev.data instanceof ArrayBuffer) {
      bytesReceived.current += ev.data.byteLength
      frameCount.current++
      const blob = new Blob([ev.data], { type: 'image/jpeg' })
      const url = URL.createObjectURL(blob)
      const img = new Image()
      img.onload = () => {
        const canvas = canvasRef.current
        if (canvas) {
          const ctx = canvas.getContext('2d')
          if (ctx) {
            canvas.width = img.width
            canvas.height = img.height
            ctx.drawImage(img, 0, 0)
          }
        }
        URL.revokeObjectURL(url)
      }
      img.src = url
    }
  }, [])

  const { sendJSON, latency } = useWebSocket({
    url: '/ws/screen',
    token,
    onMessage: handleMessage,
  })

  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now()
      const elapsed = (now - lastStatsTime.current) / 1000
      const bandwidth = bytesReceived.current / elapsed / 1024
      const currentFps = frameCount.current / elapsed
      onStatsUpdate({ bandwidth, latency, fps: currentFps })
      bytesReceived.current = 0
      frameCount.current = 0
      lastStatsTime.current = now
    }, 1000)
    return () => clearInterval(interval)
  }, [latency, onStatsUpdate])

  const getRelativeCoords = (e: React.MouseEvent) => {
    const canvas = canvasRef.current
    if (!canvas) return { x: 0, y: 0 }
    const rect = canvas.getBoundingClientRect()
    return {
      x: (e.clientX - rect.left) / rect.width,
      y: (e.clientY - rect.top) / rect.height,
    }
  }

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isController) return
    const { x, y } = getRelativeCoords(e)
    sendJSON({ type: 'mouse_event', x, y, button: 'none', action: 'move' })
  }

  const handleMouseDown = (e: React.MouseEvent) => {
    if (!isController) return
    const { x, y } = getRelativeCoords(e)
    const button = e.button === 0 ? 'left' : e.button === 2 ? 'right' : 'middle'
    sendJSON({ type: 'mouse_event', x, y, button, action: 'down' })
  }

  const handleMouseUp = (e: React.MouseEvent) => {
    if (!isController) return
    const { x, y } = getRelativeCoords(e)
    const button = e.button === 0 ? 'left' : e.button === 2 ? 'right' : 'middle'
    sendJSON({ type: 'mouse_event', x, y, button, action: 'up' })
  }

  const handleWheel = (e: React.WheelEvent) => {
    if (!isController) return
    e.preventDefault()
    const { x, y } = getRelativeCoords(e)
    sendJSON({ type: 'mouse_event', x, y, button: 'none', action: 'scroll', scrollX: e.deltaX, scrollY: e.deltaY })
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isController) return
    e.preventDefault()
    sendJSON({
      type: 'keyboard_event',
      key: e.key,
      code: e.code,
      action: 'down',
      modifiers: { ctrl: e.ctrlKey, alt: e.altKey, shift: e.shiftKey, meta: e.metaKey },
    })
  }

  const handleKeyUp = (e: React.KeyboardEvent) => {
    if (!isController) return
    e.preventDefault()
    sendJSON({
      type: 'keyboard_event',
      key: e.key,
      code: e.code,
      action: 'up',
      modifiers: { ctrl: e.ctrlKey, alt: e.altKey, shift: e.shiftKey, meta: e.metaKey },
    })
  }

  const requestControl = () => sendJSON({ type: 'control_request' })

  const sendSpecialKey = (key: string) => sendJSON({ type: 'special_key', key })

  const updateConfig = (newFps?: number, newQuality?: number) => {
    const update: { type: string; fps?: number; quality?: number } = { type: 'config_update' }
    if (newFps !== undefined) {
      setFps(newFps)
      update.fps = newFps
    }
    if (newQuality !== undefined) {
      setQuality(newQuality)
      update.quality = newQuality
    }
    sendJSON(update)
  }

  const switchMonitor = (index: number) => sendJSON({ type: 'monitor_switch', index })

  const toggleFullscreen = () => {
    if (document.fullscreenElement) {
      document.exitFullscreen()
    } else {
      containerRef.current?.requestFullscreen()
    }
  }

  return (
    <div ref={containerRef} className="relative h-full flex flex-col bg-black">
      {showToolbar && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10 flex items-center gap-2 bg-[var(--bg-secondary)]/90 backdrop-blur rounded-lg p-2 shadow-lg">
          {monitors.length > 1 && (
            <div className="flex items-center gap-1 px-2 border-r border-[var(--border)]">
              <Monitor className="w-4 h-4" />
              {monitors.map((m) => (
                <button
                  key={m.index}
                  onClick={() => switchMonitor(m.index)}
                  className={`px-2 py-1 text-xs rounded ${
                    screenInfo?.monitorIndex === m.index ? 'bg-[var(--accent)] text-white' : 'hover:bg-[var(--bg-tertiary)]'
                  }`}
                >
                  {m.index + 1}
                </button>
              ))}
            </div>
          )}
          <div className="flex items-center gap-2 px-2 border-r border-[var(--border)]">
            <label className="text-xs">{t('desktop.quality')}</label>
            <input
              type="range"
              min="20"
              max="95"
              value={quality}
              onChange={(e) => updateConfig(undefined, Number(e.target.value))}
              className="w-20 h-1"
            />
            <span className="text-xs w-8">{quality}%</span>
          </div>
          <div className="flex items-center gap-2 px-2 border-r border-[var(--border)]">
            <label className="text-xs">{t('desktop.framerate')}</label>
            <input
              type="range"
              min="5"
              max="30"
              value={fps}
              onChange={(e) => updateConfig(Number(e.target.value))}
              className="w-16 h-1"
            />
            <span className="text-xs w-6">{fps}</span>
          </div>
          <div className="flex items-center gap-1 px-2 border-r border-[var(--border)]">
            <Keyboard className="w-4 h-4" />
            <button onClick={() => sendSpecialKey('ctrl_alt_del')} className="px-2 py-1 text-xs hover:bg-[var(--bg-tertiary)] rounded">
              {t('desktop.ctrlAltDel')}
            </button>
            <button onClick={() => sendSpecialKey('win')} className="px-2 py-1 text-xs hover:bg-[var(--bg-tertiary)] rounded">
              {t('desktop.winKey')}
            </button>
          </div>
          <button onClick={toggleFullscreen} className="p-2 hover:bg-[var(--bg-tertiary)] rounded" title={t('desktop.fullscreen')}>
            <Maximize className="w-4 h-4" />
          </button>
          <button
            onClick={requestControl}
            className={`px-3 py-1 text-xs rounded ${isController ? 'bg-[var(--success)] text-white' : 'bg-[var(--accent)] text-white'}`}
          >
            {isController ? t('desktop.controlling') : t('desktop.requestControl')}
          </button>
        </div>
      )}

      <button
        onClick={() => setShowToolbar(!showToolbar)}
        className="absolute top-4 right-4 z-10 p-2 bg-[var(--bg-secondary)]/90 backdrop-blur rounded-lg shadow"
      >
        <Settings2 className="w-4 h-4" />
      </button>

      <div className="flex-1 flex items-center justify-center overflow-hidden">
        <canvas
          ref={canvasRef}
          tabIndex={0}
          className="max-w-full max-h-full object-contain cursor-crosshair focus:outline-none"
          onMouseMove={handleMouseMove}
          onMouseDown={handleMouseDown}
          onMouseUp={handleMouseUp}
          onWheel={handleWheel}
          onKeyDown={handleKeyDown}
          onKeyUp={handleKeyUp}
          onContextMenu={(e) => e.preventDefault()}
        />
      </div>
    </div>
  )
}
