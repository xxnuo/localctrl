import { useTranslation } from 'react-i18next'
import { Wifi, Clock, Activity } from 'lucide-react'

interface Props {
  stats: { bandwidth: number; latency: number; fps: number }
}

export default function StatusBar({ stats }: Props) {
  const { t } = useTranslation()

  return (
    <div className="flex items-center justify-between px-4 py-2 bg-[var(--bg-secondary)] border-t border-[var(--border)] text-xs">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1">
          <Wifi className="w-3 h-3 text-[var(--success)]" />
          <span>{t('panel.connected')}</span>
        </div>
      </div>
      <div className="flex items-center gap-4 text-[var(--text-secondary)]">
        <div className="flex items-center gap-1">
          <Activity className="w-3 h-3" />
          <span>{t('panel.bandwidth')}: {stats.bandwidth.toFixed(1)} KB/s</span>
        </div>
        <div className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          <span>{t('panel.latency')}: {stats.latency}ms</span>
        </div>
        <div>
          <span>{t('panel.fps')}: {stats.fps.toFixed(1)}</span>
        </div>
      </div>
    </div>
  )
}
