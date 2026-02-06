import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Terminal as XTerm } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import { Plus, X } from 'lucide-react'
import '@xterm/xterm/css/xterm.css'

interface Tab {
  id: string
  title: string
}

export default function TerminalView() {
  const { t } = useTranslation()
  const [tabs, setTabs] = useState<Tab[]>([{ id: 'term-1', title: 'Terminal 1' }])
  const [activeTab, setActiveTab] = useState('term-1')
  const termRefs = useRef<Map<string, { term: XTerm; ws: WebSocket; fit: FitAddon }>>(new Map())
  const containerRef = useRef<HTMLDivElement>(null)

  const token = localStorage.getItem('localctrl-token')

  useEffect(() => {
    return () => {
      termRefs.current.forEach((ref) => {
        ref.ws.close()
        ref.term.dispose()
      })
    }
  }, [])

  useEffect(() => {
    const currentRef = termRefs.current.get(activeTab)
    if (currentRef) {
      setTimeout(() => currentRef.fit.fit(), 0)
    }
  }, [activeTab])

  const initTerminal = (id: string, element: HTMLDivElement | null) => {
    if (!element || termRefs.current.has(id)) return

    const term = new XTerm({
      cursorBlink: true,
      fontSize: 14,
      fontFamily: 'Menlo, Monaco, "Courier New", monospace',
      theme: {
        background: '#1a1a2e',
        foreground: '#eee',
        cursor: '#fff',
      },
    })
    const fit = new FitAddon()
    term.loadAddon(fit)
    term.open(element)
    fit.fit()

    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${protocol}//${location.host}/ws/terminal/${id}?token=${token}`)
    ws.binaryType = 'arraybuffer'

    ws.onopen = () => {
      term.writeln('Connected to terminal...')
      ws.send(JSON.stringify({ type: 'resize', rows: term.rows, cols: term.cols }))
    }

    ws.onmessage = (ev) => {
      if (ev.data instanceof ArrayBuffer) {
        term.write(new Uint8Array(ev.data))
      }
    }

    ws.onclose = () => {
      term.writeln('\r\n\x1b[31mConnection closed\x1b[0m')
    }

    term.onData((data) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(new TextEncoder().encode(data))
      }
    })

    term.onResize(({ rows, cols }) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'resize', rows, cols }))
      }
    })

    termRefs.current.set(id, { term, ws, fit })
  }

  const addTab = () => {
    const id = `term-${Date.now()}`
    setTabs((prev) => [...prev, { id, title: `Terminal ${prev.length + 1}` }])
    setActiveTab(id)
  }

  const closeTab = (id: string) => {
    const ref = termRefs.current.get(id)
    if (ref) {
      ref.ws.close()
      ref.term.dispose()
      termRefs.current.delete(id)
    }
    setTabs((prev) => {
      const filtered = prev.filter((t) => t.id !== id)
      if (filtered.length === 0) {
        const newId = `term-${Date.now()}`
        setActiveTab(newId)
        return [{ id: newId, title: 'Terminal 1' }]
      }
      if (activeTab === id) {
        setActiveTab(filtered[0].id)
      }
      return filtered
    })
  }

  useEffect(() => {
    const handleResize = () => {
      termRefs.current.forEach((ref) => ref.fit.fit())
    }
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  return (
    <div className="h-full flex flex-col bg-[#1a1a2e]">
      <div className="flex items-center bg-[var(--bg-secondary)] border-b border-[var(--border)]">
        <div className="flex-1 flex overflow-x-auto">
          {tabs.map((tab) => (
            <div
              key={tab.id}
              className={`flex items-center gap-2 px-4 py-2 border-r border-[var(--border)] cursor-pointer ${
                activeTab === tab.id ? 'bg-[#1a1a2e] text-white' : 'hover:bg-[var(--bg-tertiary)]'
              }`}
              onClick={() => setActiveTab(tab.id)}
            >
              <span className="text-sm truncate max-w-[100px]">{tab.title}</span>
              <button
                onClick={(e) => { e.stopPropagation(); closeTab(tab.id) }}
                className="p-0.5 hover:bg-[var(--bg-tertiary)] rounded"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
        <button onClick={addTab} className="p-2 hover:bg-[var(--bg-tertiary)]" title={t('terminal.newTab')}>
          <Plus className="w-5 h-5" />
        </button>
      </div>
      <div ref={containerRef} className="flex-1 relative">
        {tabs.map((tab) => (
          <div
            key={tab.id}
            ref={(el) => initTerminal(tab.id, el)}
            className={`absolute inset-0 p-2 ${activeTab === tab.id ? 'block' : 'hidden'}`}
          />
        ))}
      </div>
    </div>
  )
}
