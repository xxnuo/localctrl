import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { FolderOpen, File, ChevronRight, Upload, FolderPlus, Trash2, Edit, Download, ArrowUp } from 'lucide-react'
import type { FileEntry } from '../types/protocol'

export default function FileManager() {
  const { t } = useTranslation()
  const [currentPath, setCurrentPath] = useState('')
  const [files, setFiles] = useState<FileEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState<string[]>([])
  const [dragOver, setDragOver] = useState(false)

  const token = localStorage.getItem('localctrl-token')

  const loadFiles = useCallback(async (path: string) => {
    setLoading(true)
    try {
      const res = await fetch(`/api/files?path=${encodeURIComponent(path)}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      const data = await res.json()
      setCurrentPath(data.path)
      setFiles(data.files || [])
      setSelected([])
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => {
    loadFiles('')
  }, [loadFiles])

  const handleNavigate = (path: string) => loadFiles(path)

  const handleGoUp = () => {
    const parent = currentPath.split('/').slice(0, -1).join('/')
    loadFiles(parent || '/')
  }

  const handleCreateFolder = async () => {
    const name = prompt(t('files.newFolder'))
    if (!name) return
    await fetch('/api/files/mkdir', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: `${currentPath}/${name}` }),
    })
    loadFiles(currentPath)
  }

  const handleDelete = async () => {
    if (!selected.length || !confirm('Delete selected items?')) return
    for (const path of selected) {
      await fetch('/api/files/delete', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ path }),
      })
    }
    loadFiles(currentPath)
  }

  const handleRename = async (file: FileEntry) => {
    const newName = prompt(t('files.rename'), file.name)
    if (!newName || newName === file.name) return
    await fetch('/api/files/rename', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ oldPath: file.path, newName }),
    })
    loadFiles(currentPath)
  }

  const handleDownload = (file: FileEntry) => {
    window.open(`/api/files/download?path=${encodeURIComponent(file.path)}&token=${token}`, '_blank')
  }

  const handleUpload = async (fileList: FileList) => {
    for (const file of Array.from(fileList)) {
      const formData = new FormData()
      formData.append('file', file)
      await fetch(`/api/files/upload?path=${encodeURIComponent(currentPath)}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      })
    }
    loadFiles(currentPath)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    if (e.dataTransfer.files.length) {
      handleUpload(e.dataTransfer.files)
    }
  }

  const toggleSelect = (path: string) => {
    setSelected((prev) => (prev.includes(path) ? prev.filter((p) => p !== path) : [...prev, path]))
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`
    return `${(bytes / 1024 / 1024 / 1024).toFixed(1)} GB`
  }

  return (
    <div
      className="h-full flex flex-col p-4"
      onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
    >
      <div className="flex items-center gap-2 mb-4 flex-wrap">
        <button onClick={handleGoUp} className="p-2 hover:bg-[var(--bg-secondary)] rounded" title="Go up">
          <ArrowUp className="w-5 h-5" />
        </button>
        <div className="flex-1 flex items-center gap-1 bg-[var(--bg-secondary)] rounded-lg px-3 py-2 text-sm overflow-x-auto">
          <span className="text-[var(--text-secondary)]">{t('files.path')}:</span>
          <span className="font-mono">{currentPath}</span>
        </div>
        <label className="p-2 hover:bg-[var(--bg-secondary)] rounded cursor-pointer" title={t('files.upload')}>
          <Upload className="w-5 h-5" />
          <input type="file" multiple className="hidden" onChange={(e) => e.target.files && handleUpload(e.target.files)} />
        </label>
        <button onClick={handleCreateFolder} className="p-2 hover:bg-[var(--bg-secondary)] rounded" title={t('files.newFolder')}>
          <FolderPlus className="w-5 h-5" />
        </button>
        {selected.length > 0 && (
          <button onClick={handleDelete} className="p-2 hover:bg-[var(--bg-secondary)] rounded text-[var(--danger)]" title={t('files.delete')}>
            <Trash2 className="w-5 h-5" />
          </button>
        )}
      </div>

      {dragOver && (
        <div className="absolute inset-0 bg-[var(--accent)]/20 flex items-center justify-center z-10 pointer-events-none">
          <div className="text-[var(--accent)] text-lg font-medium">{t('files.dropHere')}</div>
        </div>
      )}

      <div className="flex-1 overflow-auto bg-[var(--bg-secondary)] rounded-lg">
        {loading ? (
          <div className="p-8 text-center text-[var(--text-secondary)]">Loading...</div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-[var(--bg-tertiary)] sticky top-0">
              <tr>
                <th className="w-8 p-3"></th>
                <th className="text-left p-3 font-medium">{t('files.name')}</th>
                <th className="text-right p-3 font-medium w-24">{t('files.size')}</th>
                <th className="text-right p-3 font-medium w-40 hidden sm:table-cell">{t('files.modified')}</th>
                <th className="w-24 p-3"></th>
              </tr>
            </thead>
            <tbody>
              {files.map((file) => (
                <tr
                  key={file.path}
                  className={`border-t border-[var(--border)] hover:bg-[var(--bg-primary)]/50 ${selected.includes(file.path) ? 'bg-[var(--accent)]/10' : ''}`}
                  onDoubleClick={() => file.isDir && handleNavigate(file.path)}
                >
                  <td className="p-3">
                    <input
                      type="checkbox"
                      checked={selected.includes(file.path)}
                      onChange={() => toggleSelect(file.path)}
                      className="rounded"
                    />
                  </td>
                  <td className="p-3">
                    <div className="flex items-center gap-2">
                      {file.isDir ? <FolderOpen className="w-5 h-5 text-[var(--accent)]" /> : <File className="w-5 h-5 text-[var(--text-secondary)]" />}
                      <button
                        onClick={() => file.isDir && handleNavigate(file.path)}
                        className={`truncate ${file.isDir ? 'hover:text-[var(--accent)] cursor-pointer' : ''}`}
                      >
                        {file.name}
                      </button>
                      {file.isDir && <ChevronRight className="w-4 h-4 text-[var(--text-secondary)]" />}
                    </div>
                  </td>
                  <td className="p-3 text-right text-[var(--text-secondary)]">{file.isDir ? '-' : formatSize(file.size)}</td>
                  <td className="p-3 text-right text-[var(--text-secondary)] hidden sm:table-cell">{file.modTime}</td>
                  <td className="p-3">
                    <div className="flex justify-end gap-1">
                      <button onClick={() => handleRename(file)} className="p-1 hover:bg-[var(--bg-tertiary)] rounded" title={t('files.rename')}>
                        <Edit className="w-4 h-4" />
                      </button>
                      {!file.isDir && (
                        <button onClick={() => handleDownload(file)} className="p-1 hover:bg-[var(--bg-tertiary)] rounded" title={t('files.download')}>
                          <Download className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
