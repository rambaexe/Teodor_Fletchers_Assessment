import { useRef, useState, type DragEvent } from 'react'
import { ACCEPTED_EXTENSIONS, api, isAccepted, type DocumentSummary } from '../api'
import type { Notify } from '../useToasts'

interface Props {
  onUploaded: (docs: DocumentSummary[]) => void
  notify: Notify
}

export function UploadArea({ onUploaded, notify }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(0)

  const uploadAll = async (fileList: FileList | null) => {
    if (!fileList?.length) return
    const files = [...fileList]

    // quick client-side check; backend still verifies the actual content
    for (const f of files.filter((f) => !isAccepted(f))) {
      notify(`${f.name}: unsupported file type. Only PDF and Word (.docx) files are accepted.`)
    }
    const accepted = files.filter(isAccepted)
    if (!accepted.length) return

    setUploading(accepted.length)
    const results = await Promise.allSettled(accepted.map((f) => api.upload(f)))
    setUploading(0)

    const uploaded: DocumentSummary[] = []
    results.forEach((r, i) => {
      if (r.status === 'fulfilled') uploaded.push(r.value)
      else notify(`${accepted[i].name}: upload failed. ${(r.reason as Error).message}`)
    })
    onUploaded(uploaded)
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
        accept={ACCEPTED_EXTENSIONS.join(',')}
        multiple
        hidden
        onChange={(e) => {
          uploadAll(e.target.files)
          e.target.value = '' // allow re-uploading the same file
        }}
      />
      <strong>{uploading ? `Uploading ${uploading} file(s)…` : 'Drop files here or click to browse'}</strong>
      <span className="muted">PDF or Word (.docx)</span>
    </div>
  )
}
