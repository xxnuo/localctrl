import { useState, useEffect } from 'react'
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../hooks/useAuth'
import { Monitor, FolderOpen, Terminal, Network, MessageSquare, Settings, LogOut, Sun, Moon, Menu, X } from 'lucide-react'
import RemoteDesktop from '../components/RemoteDesktop'
import FileManager from '../components/FileManager'
import TerminalView from '../components/Terminal'
import PortForward from '../components/PortForward'
import Chat from '../components/Chat'
import SettingsView from '../components/Settings'
import StatusBar from '../components/StatusBar'
import type { SysInfo } from '../types/protocol'

export default function Panel() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()
  const { logout } = useAuth()
  const [sysInfo, setSysInfo] = useState<SysInfo | null>(null)
  const [theme, setTheme] = useState(() => localStorage.getItem('localctrl-theme') || 'system')
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [stats, setStats] = useState({ bandwidth: 0, latency: 0, fps: 0 })

  useEffect(() => {
    const token = localStorage.getItem('localctrl-token')
    fetch('/api/sysinfo', { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => r.json())
      .then(setSysInfo)
      .catch(console.error)
  }, [])

  useEffect(() => {
    const root = document.documentElement
    if (theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
    localStorage.setItem('localctrl-theme', theme)
  }, [theme])

  const navItems = [
    { path: '/', icon: Monitor, label: t('panel.desktop') },
    { path: '/files', icon: FolderOpen, label: t('panel.files') },
    { path: '/terminal', icon: Terminal, label: t('panel.terminal') },
    { path: '/proxy', icon: Network, label: t('panel.portForward') },
    { path: '/chat', icon: MessageSquare, label: t('panel.chat') },
    { path: '/settings', icon: Settings, label: t('panel.settings') },
  ]

  const currentPath = location.pathname === '' ? '/' : location.pathname

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const NavButton = ({ item, mobile = false }: { item: typeof navItems[0]; mobile?: boolean }) => {
    const isActive = currentPath === item.path || (item.path !== '/' && currentPath.startsWith(item.path))
    const Icon = item.icon
    return (
      <button
        onClick={() => {
          navigate(item.path)
          if (mobile) setMobileMenuOpen(false)
        }}
        className={`flex items-center gap-3 w-full px-4 py-3 rounded-lg transition ${
          isActive
            ? 'bg-[var(--accent)] text-white'
            : 'hover:bg-[var(--bg-tertiary)] text-[var(--text-primary)]'
        } ${mobile ? 'text-base' : 'text-sm'}`}
        title={item.label}
      >
        <Icon className="w-5 h-5 flex-shrink-0" />
        <span className={mobile ? '' : 'hidden lg:inline'}>{item.label}</span>
      </button>
    )
  }

  return (
    <div className="h-screen flex flex-col bg-[var(--bg-primary)]">
      <div className="flex flex-1 overflow-hidden">
        <aside className="hidden md:flex flex-col w-16 lg:w-56 bg-[var(--bg-secondary)] border-r border-[var(--border)] p-3">
          <div className="flex items-center gap-2 px-2 mb-6">
            <Monitor className="w-8 h-8 text-[var(--accent)]" />
            <span className="hidden lg:block font-bold text-lg">LocalCtrl</span>
          </div>
          {sysInfo && (
            <div className="hidden lg:block px-2 mb-4 text-xs text-[var(--text-secondary)]">
              <p className="truncate font-medium text-[var(--text-primary)]">{sysInfo.hostname}</p>
              <p className="truncate">{sysInfo.os}</p>
            </div>
          )}
          <nav className="flex-1 space-y-1">
            {navItems.map((item) => (
              <NavButton key={item.path} item={item} />
            ))}
          </nav>
          <div className="mt-auto space-y-2">
            <button
              onClick={() => setTheme(theme === 'dark' ? 'light' : theme === 'light' ? 'system' : 'dark')}
              className="flex items-center gap-3 w-full px-4 py-3 rounded-lg hover:bg-[var(--bg-tertiary)] text-sm"
            >
              {theme === 'dark' ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
              <span className="hidden lg:inline">{t(`settings.theme${theme.charAt(0).toUpperCase() + theme.slice(1)}`)}</span>
            </button>
            <button
              onClick={handleLogout}
              className="flex items-center gap-3 w-full px-4 py-3 rounded-lg hover:bg-[var(--bg-tertiary)] text-[var(--danger)] text-sm"
            >
              <LogOut className="w-5 h-5" />
              <span className="hidden lg:inline">Logout</span>
            </button>
          </div>
        </aside>

        <main className="flex-1 flex flex-col overflow-hidden">
          <div className="md:hidden flex items-center justify-between p-3 bg-[var(--bg-secondary)] border-b border-[var(--border)]">
            <div className="flex items-center gap-2">
              <Monitor className="w-6 h-6 text-[var(--accent)]" />
              <span className="font-bold">LocalCtrl</span>
            </div>
            <button onClick={() => setMobileMenuOpen(true)} className="p-2">
              <Menu className="w-6 h-6" />
            </button>
          </div>

          <div className="flex-1 overflow-auto">
            <Routes>
              <Route path="/" element={<RemoteDesktop onStatsUpdate={setStats} />} />
              <Route path="/files" element={<FileManager />} />
              <Route path="/terminal" element={<TerminalView />} />
              <Route path="/proxy" element={<PortForward />} />
              <Route path="/chat" element={<Chat />} />
              <Route path="/settings" element={<SettingsView theme={theme} setTheme={setTheme} />} />
            </Routes>
          </div>
        </main>
      </div>

      <StatusBar stats={stats} />

      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div className="absolute inset-0 bg-black/50" onClick={() => setMobileMenuOpen(false)} />
          <div className="absolute right-0 top-0 bottom-0 w-64 bg-[var(--bg-secondary)] p-4 flex flex-col">
            <div className="flex justify-between items-center mb-6">
              <span className="font-bold text-lg">Menu</span>
              <button onClick={() => setMobileMenuOpen(false)}>
                <X className="w-6 h-6" />
              </button>
            </div>
            <nav className="flex-1 space-y-2">
              {navItems.map((item) => (
                <NavButton key={item.path} item={item} mobile />
              ))}
            </nav>
            <button
              onClick={handleLogout}
              className="flex items-center gap-3 w-full px-4 py-3 rounded-lg hover:bg-[var(--bg-tertiary)] text-[var(--danger)]"
            >
              <LogOut className="w-5 h-5" />
              Logout
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
