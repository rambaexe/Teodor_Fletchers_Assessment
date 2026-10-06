import { useRef, useState, type DragEvent } from 'react'
import { api } from '../api'

const ACCEPT = '.pdf,.docx'

export function UploadArea({ onUploaded }: { onUploaded: () => void }) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const uploadAll = async (files: FileList | null) => {
    if (!files?.length) return
    setError(null)
    setUploading(files.length)
    // backend detects type from content; accept list is just a UX hint
    const results = await Promise.allSettled([...files].map((f) => api.upload(f)))
    setUploading(0)
    const failed = results.filter((r) => r.status === 'rejected').length
    if (failed) setError(`${failed} upload(s) failed`)
    onUploaded()
  }

  const onDrop = (e: DragEvent) => {
    e.preventDefault()
    setDragging(false)
    uploadAll(e.dataTransfer.files)
  }

  return (
    <div
      className={dragging ? 'upload dragging' : 'upload'}
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault()
        setDragging(true)
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT}
        multiple
        hidden
        onChange={(e) => {
          uploadAll(e.target.files)
          e.target.value = '' // allow re-uploading the same file
        }}
      />
      <strong>{uploading ? `Uploading ${uploading} file(s)…` : 'Drop files here or click to browse'}</strong>
      <span className="muted">PDF or Word (.docx)</span>
      {error && <span className="error">{error}</span>}
    </div>
  )
}
