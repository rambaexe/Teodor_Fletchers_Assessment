import { useCallback, useEffect, useRef, useState } from 'react'
import { api, isActive, type DocumentSummary, type Status } from './api'
import { DocumentDetail } from './components/DocumentDetail'
import { DocumentTable } from './components/DocumentTable'
import { Toasts } from './components/Toasts'
import { useToasts } from './useToasts'
import { UploadArea } from './components/UploadArea'

const POLL_MS = 1000
const BACKEND_DOWN = 'backend-down' // toast id

export default function App() {
  const [documents, setDocuments] = useState<DocumentSummary[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [backendDown, setBackendDown] = useState(false)
  const { toasts, notify, dismiss } = useToasts()

  // last seen status per doc; used to toast docs that just failed
  const lastStatus = useRef(new Map<string, Status>())

  const refresh = useCallback(async () => {
    try {
      const docs = await api.list()
      for (const d of docs) {
        const prev = lastStatus.current.get(d.id)
        if (d.status === 'failed' && prev && prev !== 'failed') {
          notify(`${d.filename}: ${d.error ?? 'processing failed'}`)
        }
      }
      lastStatus.current = new Map(docs.map((d) => [d.id, d.status]))
      setDocuments(docs)
      setBackendDown(false)
      dismiss(BACKEND_DOWN)
    } catch {
      setBackendDown(true)
      notify('Cannot reach the backend. Retrying…', { id: BACKEND_DOWN, sticky: true })
    }
  }, [notify, dismiss])

  useEffect(() => {
    refresh()
  }, [refresh])

  // poll while something is processing, or until the backend is back
  const shouldPoll = backendDown || documents.some(isActive)
  useEffect(() => {
    if (!shouldPoll) return
    const timer = setInterval(refresh, POLL_MS)
    return () => clearInterval(timer)
  }, [shouldPoll, refresh])

  const handleUploaded = (docs: DocumentSummary[]) => {
    for (const d of docs) lastStatus.current.set(d.id, d.status)
    refresh()
  }

  const handleDelete = async (doc: DocumentSummary) => {
    try {
      await api.remove(doc.id)
      if (doc.id === selectedId) setSelectedId(null)
    } catch (e) {
      notify(`Could not delete ${doc.filename}. ${(e as Error).message}`)
    }
    refresh()
  }

  const selected = documents.find((d) => d.id === selectedId)

  return (
    <div className="app">
      <header>
        <h1>Document Ingestion</h1>
        <p className="muted">Upload PDF or Word files to extract content from.</p>
      </header>

      <UploadArea onUploaded={handleUploaded} notify={notify} />

      <div className={selected ? 'layout with-detail' : 'layout'}>
        <DocumentTable
          documents={documents}
          selectedId={selectedId}
          onSelect={setSelectedId}
          onDelete={handleDelete}
        />
        {selected && <DocumentDetail summary={selected} onClose={() => setSelectedId(null)} />}
      </div>

      <Toasts toasts={toasts} onDismiss={dismiss} />
    </div>
  )
}
