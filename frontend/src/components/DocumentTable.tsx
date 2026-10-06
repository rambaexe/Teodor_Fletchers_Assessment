import { isActive, typeLabel, type DocumentSummary } from '../api'

interface Props {
  documents: DocumentSummary[]
  selectedId: string | null
  onSelect: (id: string) => void
  onDelete: (id: string) => void
}

export function DocumentTable({ documents, selectedId, onSelect, onDelete }: Props) {
  if (!documents.length) {
    return <div className="card empty muted">No documents yet. Upload one to get started.</div>
  }

  return (
    <div className="card table-wrap">
      <table>
        <thead>
          <tr>
            <th>File</th>
            <th>Type</th>
            <th>Status</th>
            <th>Method</th>
            <th>Category</th>
            <th>Uploaded</th>
            <th aria-label="actions" />
          </tr>
        </thead>
        <tbody>
          {documents.map((d) => (
            <tr
              key={d.id}
              className={d.id === selectedId ? 'selected' : undefined}
              onClick={() => onSelect(d.id)}
            >
              <td className="filename" title={d.filename}>
                {d.filename}
              </td>
              <td>{typeLabel(d.file_type)}</td>
              <td>
                <StatusCell doc={d} />
              </td>
              <td>{d.extraction_method ? <span className="tag">{d.extraction_method}</span> : '—'}</td>
              <td>{d.category ?? '—'}</td>
              <td className="muted">{new Date(d.created_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}</td>
              <td>
                <button
                  className="icon-btn"
                  title="Delete"
                  onClick={(e) => {
                    e.stopPropagation()
                    onDelete(d.id)
                  }}
                >
                  ✕
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function StatusCell({ doc }: { doc: DocumentSummary }) {
  return (
    <div className="status-cell" title={doc.error ?? undefined}>
      <span className={`badge ${doc.status}`}>{doc.status}</span>
      {isActive(doc) && (
        <div className="progress">
          <div style={{ width: `${doc.progress}%` }} />
        </div>
      )}
    </div>
  )
}
