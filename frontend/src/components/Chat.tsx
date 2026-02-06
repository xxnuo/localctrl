import { useState, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { Send, MessageSquare } from 'lucide-react'
import type { ChatMessage } from '../types/protocol'

export default function Chat() {
  const { t } = useTranslation()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const wsRef = useRef<WebSocket | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const token = localStorage.getItem('localctrl-token')

  useEffect(() => {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${protocol}//${location.host}/ws/chat?token=${token}`)
    wsRef.current = ws

    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data) as ChatMessage
        setMessages((prev) => [...prev, msg])
      } catch {}
    }

    return () => ws.close()
  }, [token])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = () => {
    if (!input.trim() || !wsRef.current) return
    wsRef.current.send(JSON.stringify({ text: input }))
    setInput('')
  }

  const formatTime = (ts: number) => {
    const d = new Date(ts)
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className="h-full flex flex-col p-4">
      <h1 className="text-xl font-bold mb-4 flex items-center gap-2">
        <MessageSquare className="w-6 h-6" />
        {t('panel.chat')}
      </h1>

      <div className="flex-1 overflow-auto bg-[var(--bg-secondary)] rounded-lg p-4 space-y-3">
        {messages.map((msg) => (
          <div key={msg.id} className="flex flex-col">
            <div className="flex items-baseline gap-2">
              <span className="font-medium text-[var(--accent)]">{msg.sender}</span>
              <span className="text-xs text-[var(--text-secondary)]">{formatTime(msg.timestamp)}</span>
            </div>
            <p className="text-sm mt-1">{msg.text}</p>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="flex gap-2 mt-4">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder={t('chat.placeholder')}
          className="flex-1 px-4 py-3 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] focus:border-[var(--accent)] focus:outline-none"
        />
        <button
          onClick={handleSend}
          className="px-4 py-3 bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white rounded-lg"
        >
          <Send className="w-5 h-5" />
        </button>
      </div>
    </div>
  )
}
