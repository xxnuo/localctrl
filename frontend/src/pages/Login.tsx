import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../hooks/useAuth'
import { Monitor, Globe } from 'lucide-react'

export default function Login() {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const { setToken } = useAuth()
  const [tab, setTab] = useState<'quick' | 'account'>('quick')
  const [isRegister, setIsRegister] = useState(false)
  const [password, setPassword] = useState('')
  const [username, setUsername] = useState('')
  const [userPassword, setUserPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const toggleLang = () => {
    const newLang = i18n.language === 'zh' ? 'en' : 'zh'
    i18n.changeLanguage(newLang)
    localStorage.setItem('localctrl-lang', newLang)
  }

  const handleQuickConnect = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: 'password', password }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error)
      setToken(data.token)
      navigate('/')
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Connection failed')
    } finally {
      setLoading(false)
    }
  }

  const handleAccountLogin = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: 'account', username, password: userPassword }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error)
      setToken(data.token)
      navigate('/')
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async () => {
    if (userPassword !== confirmPassword) {
      setError('Passwords do not match')
      return
    }
    setLoading(true)
    setError('')
    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password: userPassword }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error)
      setToken(data.token)
      navigate('/')
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--bg-secondary)] p-4">
      <div className="w-full max-w-md">
        <div className="bg-[var(--bg-primary)] rounded-2xl shadow-xl p-8">
          <div className="flex items-center justify-center mb-6">
            <Monitor className="w-10 h-10 text-[var(--accent)] mr-3" />
            <div>
              <h1 className="text-2xl font-bold">{t('login.title')}</h1>
              <p className="text-sm text-[var(--text-secondary)]">{t('login.subtitle')}</p>
            </div>
          </div>

          <button
            onClick={toggleLang}
            className="absolute top-4 right-4 p-2 rounded-lg hover:bg-[var(--bg-secondary)] transition"
          >
            <Globe className="w-5 h-5" />
          </button>

          {!isRegister && (
            <div className="flex mb-6 bg-[var(--bg-secondary)] rounded-lg p-1">
              <button
                className={`flex-1 py-2 rounded-md text-sm font-medium transition ${
                  tab === 'quick' ? 'bg-[var(--bg-primary)] shadow' : ''
                }`}
                onClick={() => setTab('quick')}
              >
                {t('login.quickConnect')}
              </button>
              <button
                className={`flex-1 py-2 rounded-md text-sm font-medium transition ${
                  tab === 'account' ? 'bg-[var(--bg-primary)] shadow' : ''
                }`}
                onClick={() => setTab('account')}
              >
                {t('login.accountLogin')}
              </button>
            </div>
          )}

          {error && (
            <div className="mb-4 p-3 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded-lg text-sm">
              {error}
            </div>
          )}

          {isRegister ? (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-center mb-4">{t('login.registerTitle')}</h2>
              <input
                type="text"
                placeholder={t('login.username')}
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-3 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] focus:border-[var(--accent)] focus:outline-none"
              />
              <input
                type="password"
                placeholder={t('login.userPassword')}
                value={userPassword}
                onChange={(e) => setUserPassword(e.target.value)}
                className="w-full px-4 py-3 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] focus:border-[var(--accent)] focus:outline-none"
              />
              <input
                type="password"
                placeholder={t('login.confirmPassword')}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full px-4 py-3 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] focus:border-[var(--accent)] focus:outline-none"
              />
              <button
                onClick={handleRegister}
                disabled={loading}
                className="w-full py-3 bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white rounded-lg font-medium transition disabled:opacity-50"
              >
                {loading ? '...' : t('login.register')}
              </button>
              <p className="text-center text-sm text-[var(--text-secondary)]">
                {t('login.hasAccount')}{' '}
                <button onClick={() => setIsRegister(false)} className="text-[var(--accent)] hover:underline">
                  {t('login.login')}
                </button>
              </p>
            </div>
          ) : tab === 'quick' ? (
            <div className="space-y-4">
              <input
                type="password"
                placeholder={t('login.password')}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleQuickConnect()}
                className="w-full px-4 py-3 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] focus:border-[var(--accent)] focus:outline-none"
              />
              <button
                onClick={handleQuickConnect}
                disabled={loading}
                className="w-full py-3 bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white rounded-lg font-medium transition disabled:opacity-50"
              >
                {loading ? '...' : t('login.connect')}
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <input
                type="text"
                placeholder={t('login.username')}
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-3 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] focus:border-[var(--accent)] focus:outline-none"
              />
              <input
                type="password"
                placeholder={t('login.userPassword')}
                value={userPassword}
                onChange={(e) => setUserPassword(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAccountLogin()}
                className="w-full px-4 py-3 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] focus:border-[var(--accent)] focus:outline-none"
              />
              <button
                onClick={handleAccountLogin}
                disabled={loading}
                className="w-full py-3 bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white rounded-lg font-medium transition disabled:opacity-50"
              >
                {loading ? '...' : t('login.login')}
              </button>
              <p className="text-center text-sm text-[var(--text-secondary)]">
                {t('login.noAccount')}{' '}
                <button onClick={() => setIsRegister(true)} className="text-[var(--accent)] hover:underline">
                  {t('login.register')}
                </button>
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
