import { useEffect, useState } from 'react'
import {
  api,
  formatBytes,
  formatDate,
  typeLabel,
  type DocumentDetail as Detail,
  type DocumentSummary,
} from '../api'
import { StatusCell } from './DocumentTable'

interface Props {
  summary: DocumentSummary
  onClose: () => void
}

export function DocumentDetail({ summary, onClose }: Props) {
  const [detail, setDetail] = useState<Detail | null>(null)
  const [copied, setCopied] = useState(false)

  // refetch when the doc moves through the pipeline
  useEffect(() => {
    api.get(summary.id).then(setDetail).catch(() => setDetail(null))
  }, [summary.id, summary.status, summary.progress])

  const copyText = async () => {
    await navigator.clipboard.writeText(await api.text(summary.id))
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  const d = detail?.id === summary.id ? detail : null

  return (
    <aside className="card detail">
      <div className="detail-head">
        <h2 title={summary.filename}>{summary.filename}</h2>
        <button className="icon-btn" title="Close" onClick={onClose}>
          ✕
        </button>
      </div>

      {summary.error && <div className="banner">{summary.error}</div>}

      <StatusCell doc={summary} />

      <section>
        <h3>File</h3>
        <dl className="facts">
          <Fact label="Type" value={typeLabel(summary)} />
          <Fact label="Size" value={formatBytes(summary.size_bytes)} />
          <Fact label="Pages" value={summary.page_count} />
          <Fact label="Uploaded" value={formatDate(summary.created_at)} />
          <Fact label="Updated" value={formatDate(summary.updated_at)} />
        </dl>
      </section>

      <section>
        <h3>Extraction</h3>
        <dl className="facts">
          <Fact label="Method" value={summary.extraction_method} />
          <Fact label="Category" value={summary.category} />
        </dl>
      </section>

      {d?.summary && (
        <section>
          <h3>Summary</h3>
          <p>{d.summary}</p>
        </section>
      )}

      {!!d?.keywords.length && (
        <section>
          <h3>Keywords</h3>
          <div className="tags">
            {d.keywords.map((k) => (
              <span key={k} className="tag">
                {k}
              </span>
            ))}
          </div>
        </section>
      )}

      {d && Object.keys(d.metadata).length > 0 && (
        <section>
          <h3>Metadata</h3>
          <dl className="facts">
            {Object.entries(d.metadata).map(([k, v]) => (
              <Fact key={k} label={k} value={String(v)} />
            ))}
          </dl>
        </section>
      )}

      <section>
        <div className="section-head">
          <h3>Content {d && <span className="muted">({d.chunks.length} chunks)</span>}</h3>
          {!!d?.chunks.length && (
            <button className="btn" onClick={copyText}>
              {copied ? 'Copied' : 'Copy as text'}
            </button>
          )}
        </div>
        {d?.chunks.length ? (
          <ol className="chunks">
            {d.chunks.map((c) => (
              <li key={c.position}>
                <div className="chunk-meta muted">
                  {c.kind}
                  {c.page != null && ` · page ${c.page}`}
                  {c.source === 'ocr' && <span className="tag">OCR</span>}
                </div>
                <p>{c.text}</p>
              </li>
            ))}
          </ol>
        ) : (
          <p className="muted">No content extracted yet.</p>
        )}
      </section>
    </aside>
  )
}

function Fact({ label, value }: { label: string; value: string | number | null }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value ?? '—'}</dd>
    </div>
  )
}
