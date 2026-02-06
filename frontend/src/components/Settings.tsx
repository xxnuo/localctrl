import { useTranslation } from 'react-i18next'
import { Globe, Palette } from 'lucide-react'

interface Props {
  theme: string
  setTheme: (t: string) => void
}

export default function Settings({ theme, setTheme }: Props) {
  const { t, i18n } = useTranslation()

  const handleLangChange = (lang: string) => {
    i18n.changeLanguage(lang)
    localStorage.setItem('localctrl-lang', lang)
  }

  return (
    <div className="h-full p-4 overflow-auto">
      <div className="max-w-md mx-auto space-y-6">
        <h1 className="text-xl font-bold">{t('panel.settings')}</h1>

        <div className="bg-[var(--bg-secondary)] rounded-lg p-4">
          <label className="flex items-center gap-2 text-sm font-medium mb-3">
            <Globe className="w-5 h-5" />
            {t('settings.language')}
          </label>
          <div className="flex gap-2">
            <button
              onClick={() => handleLangChange('en')}
              className={`flex-1 py-2 rounded-lg text-sm ${i18n.language === 'en' ? 'bg-[var(--accent)] text-white' : 'bg-[var(--bg-tertiary)]'}`}
            >
              English
            </button>
            <button
              onClick={() => handleLangChange('zh')}
              className={`flex-1 py-2 rounded-lg text-sm ${i18n.language === 'zh' ? 'bg-[var(--accent)] text-white' : 'bg-[var(--bg-tertiary)]'}`}
            >
              中文
            </button>
          </div>
        </div>

        <div className="bg-[var(--bg-secondary)] rounded-lg p-4">
          <label className="flex items-center gap-2 text-sm font-medium mb-3">
            <Palette className="w-5 h-5" />
            {t('settings.theme')}
          </label>
          <div className="flex gap-2">
            <button
              onClick={() => setTheme('system')}
              className={`flex-1 py-2 rounded-lg text-sm ${theme === 'system' ? 'bg-[var(--accent)] text-white' : 'bg-[var(--bg-tertiary)]'}`}
            >
              {t('settings.themeSystem')}
            </button>
            <button
              onClick={() => setTheme('light')}
              className={`flex-1 py-2 rounded-lg text-sm ${theme === 'light' ? 'bg-[var(--accent)] text-white' : 'bg-[var(--bg-tertiary)]'}`}
            >
              {t('settings.themeLight')}
            </button>
            <button
              onClick={() => setTheme('dark')}
              className={`flex-1 py-2 rounded-lg text-sm ${theme === 'dark' ? 'bg-[var(--accent)] text-white' : 'bg-[var(--bg-tertiary)]'}`}
            >
              {t('settings.themeDark')}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
