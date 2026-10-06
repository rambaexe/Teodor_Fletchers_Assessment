// mirrors backend response schemas (backend/app/main.py)

export type Status = 'queued' | 'processing' | 'done' | 'failed'

export interface DocumentSummary {
  id: string
  filename: string
  file_type: string | null
  size_bytes: number
  status: Status
  progress: number
  error: string | null
  extraction_method: string | null
  page_count: number | null
  category: string | null
  created_at: string
  updated_at: string
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
  if (!res.ok) throw new Error(await errorMessage(res))
  return res
}

// FastAPI errors look like {"detail": "..."}; fall back to the status line
async function errorMessage(res: Response): Promise<string> {
  try {
    const body = await res.json()
    if (typeof body.detail === 'string') return body.detail
  } catch {
    // not JSON
  }
  return `Request failed (${res.status} ${res.statusText})`
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

// --- display helpers ---

export const ACCEPTED_EXTENSIONS = ['.pdf', '.docx']

export const isAccepted = (f: File) =>
  ACCEPTED_EXTENSIONS.some((ext) => f.name.toLowerCase().endsWith(ext))

export const isActive = (d: DocumentSummary) => d.status === 'queued' || d.status === 'processing'

export const STATUS_LABEL: Record<Status, { label: string; hint: string }> = {
  queued: { label: 'Queued', hint: 'Added, waiting for extraction' },
  processing: { label: 'Extracting', hint: 'Content is being extracted' },
  done: { label: 'Stored', hint: 'Content extracted and stored' },
  failed: { label: 'Error', hint: 'Processing failed' },
}

// detected type wins; extension as fallback (e.g. before detection / on failure)
export function typeLabel(d: DocumentSummary): string {
  const t = d.file_type ?? d.filename.split('.').pop()?.toLowerCase()
  return t === 'pdf' ? 'PDF' : t === 'docx' ? 'Word' : '—'
}

export const formatDate = (iso: string) =>
  new Date(iso).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })

export function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`
  if (n < 1024 ** 2) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / 1024 ** 2).toFixed(1)} MB`
}
