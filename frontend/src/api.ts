// mirrors backend response schemas (backend/app/main.py)

export type Status = 'queued' | 'processing' | 'done' | 'failed'

export interface DocumentSummary {
  id: string
  filename: string
  file_type: string | null
  status: Status
  progress: number
  error: string | null
  extraction_method: string | null
  page_count: number | null
  category: string | null
  created_at: string
}

export interface Chunk {
  position: number
  text: string
  kind: string
  page: number | null
  source: string
}

export interface DocumentDetail extends DocumentSummary {
  metadata: Record<string, unknown>
  summary: string | null
  keywords: string[]
  chunks: Chunk[]
}

// /api is proxied to the backend by Vite
async function request(path: string, init?: RequestInit): Promise<Response> {
  const res = await fetch(`/api${path}`, init)
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`)
  return res
}

export const api = {
  async upload(file: File): Promise<DocumentSummary> {
    const body = new FormData()
    body.append('file', file)
    return (await request('/documents', { method: 'POST', body })).json()
  },
  list: async (): Promise<DocumentSummary[]> => (await request('/documents')).json(),
  get: async (id: string): Promise<DocumentDetail> => (await request(`/documents/${id}`)).json(),
  text: async (id: string): Promise<string> => (await request(`/documents/${id}/text`)).text(),
  remove: async (id: string): Promise<void> => {
    await request(`/documents/${id}`, { method: 'DELETE' })
  },
}

export const isActive = (d: DocumentSummary) => d.status === 'queued' || d.status === 'processing'

export const typeLabel = (t: string | null) => (t === 'pdf' ? 'PDF' : t === 'docx' ? 'Word' : '—')
