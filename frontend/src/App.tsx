import { useCallback, useEffect, useState } from 'react'
import { api, isActive, type DocumentSummary } from './api'
import { DocumentDetail } from './components/DocumentDetail'
import { DocumentTable } from './components/DocumentTable'
import { UploadArea } from './components/UploadArea'

const POLL_MS = 1000

export default function App() {
  const [documents, setDocuments] = useState<DocumentSummary[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    try {
      setDocuments(await api.list())
      setError(null)
    } catch {
      setError('Cannot reach the backend')
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  // poll only while something is still processing
  const anyActive = documents.some(isActive)
  useEffect(() => {
    if (!anyActive) return
    const timer = setInterval(refresh, POLL_MS)
    return () => clearInterval(timer)
  }, [anyActive, refresh])

  const handleDelete = async (id: string) => {
    await api.remove(id)
    if (id === selectedId) setSelectedId(null)
    refresh()
  }

  const selected = documents.find((d) => d.id === selectedId)

  return (
    <div className="app">
      <header>
        <h1>Document Ingestion</h1>
        <p className="muted">Upload PDF or Word files to extract, enrich and store their content.</p>
      </header>

      {error && <div className="banner">{error}</div>}

      <UploadArea onUploaded={refresh} />

      <div className={selected ? 'layout with-detail' : 'layout'}>
        <DocumentTable
          documents={documents}
          selectedId={selectedId}
          onSelect={setSelectedId}
          onDelete={handleDelete}
        />
        {selected && <DocumentDetail summary={selected} onClose={() => setSelectedId(null)} />}
      </div>
    </div>
  )
}
