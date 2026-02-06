import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Plus, Trash2, Network } from 'lucide-react'
import type { ProxyRule } from '../types/protocol'

export default function PortForward() {
  const { t } = useTranslation()
  const [rules, setRules] = useState<ProxyRule[]>([])
  const [pathPrefix, setPathPrefix] = useState('')
  const [target, setTarget] = useState('')
  const token = localStorage.getItem('localctrl-token')

  const loadRules = async () => {
    const res = await fetch('/api/proxy/rules', { headers: { Authorization: `Bearer ${token}` } })
    const data = await res.json()
    setRules(data || [])
  }

  useEffect(() => { loadRules() }, [])

  const handleAdd = async () => {
    if (!pathPrefix || !target) return
    await fetch('/api/proxy/rules', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ pathPrefix, target }),
    })
    setPathPrefix('')
    setTarget('')
    loadRules()
  }

  const handleDelete = async (id: string) => {
    await fetch(`/api/proxy/rules/${id}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    })
    loadRules()
  }

  return (
    <div className="h-full p-4 overflow-auto">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-xl font-bold mb-6 flex items-center gap-2">
          <Network className="w-6 h-6" />
          {t('proxy.title')}
        </h1>

        <div className="bg-[var(--bg-secondary)] rounded-lg p-4 mb-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium mb-1">{t('proxy.pathPrefix')}</label>
              <input
                type="text"
                value={pathPrefix}
                onChange={(e) => setPathPrefix(e.target.value)}
                placeholder="app1/"
                className="w-full px-3 py-2 rounded-lg bg-[var(--bg-primary)] border border-[var(--border)] focus:border-[var(--accent)] focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">{t('proxy.target')}</label>
              <input
                type="text"
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                placeholder="http://localhost:3000"
                className="w-full px-3 py-2 rounded-lg bg-[var(--bg-primary)] border border-[var(--border)] focus:border-[var(--accent)] focus:outline-none"
              />
            </div>
          </div>
          <button
            onClick={handleAdd}
            className="flex items-center gap-2 px-4 py-2 bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white rounded-lg"
          >
            <Plus className="w-4 h-4" />
            {t('proxy.add')}
          </button>
        </div>

        {rules.length === 0 ? (
          <div className="text-center text-[var(--text-secondary)] py-8">{t('proxy.noRules')}</div>
        ) : (
          <div className="space-y-2">
            {rules.map((rule) => (
              <div key={rule.id} className="flex items-center justify-between bg-[var(--bg-secondary)] rounded-lg p-4">
                <div className="flex-1">
                  <div className="font-mono text-sm">
                    <span className="text-[var(--accent)]">/proxy/{rule.pathPrefix}</span>
                    <span className="mx-2 text-[var(--text-secondary)]">→</span>
                    <span>{rule.target}</span>
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(rule.id)}
                  className="p-2 hover:bg-[var(--bg-tertiary)] rounded text-[var(--danger)]"
                  title={t('proxy.delete')}
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
