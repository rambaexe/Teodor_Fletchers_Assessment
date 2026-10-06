import { formatDate, isActive, STATUS_LABEL, typeLabel, type DocumentSummary } from '../api'

interface Props {
  documents: DocumentSummary[]
  selectedId: string | null
  onSelect: (id: string) => void
  onDelete: (doc: DocumentSummary) => void
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
            <th>Updated</th>
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
              <td>{typeLabel(d)}</td>
              <td>
                <StatusCell doc={d} />
              </td>
              <td className="muted">{formatDate(d.updated_at)}</td>
              <td className="actions">
                <button
                  className="icon-btn"
                  title="Delete"
                  onClick={(e) => {
                    e.stopPropagation()
                    onDelete(d)
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

export function StatusCell({ doc }: { doc: DocumentSummary }) {
  const { label, hint } = STATUS_LABEL[doc.status]
  return (
    <div className="status-cell" title={doc.error ?? hint}>
      <span className={`badge ${doc.status}`}>{label}</span>
      {isActive(doc) && (
        <div className="progress">
          <div style={{ width: `${doc.progress}%` }} />
        </div>
      )}
    </div>
  )
}
