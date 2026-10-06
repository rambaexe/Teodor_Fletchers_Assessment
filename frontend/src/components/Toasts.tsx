import type { Toast } from '../useToasts'

export function Toasts({ toasts, onDismiss }: { toasts: Toast[]; onDismiss: (id: string) => void }) {
  return (
    <div className="toasts" role="alert" aria-live="assertive">
      {toasts.map((t) => (
        <div key={t.id} className="toast">
          <span>{t.message}</span>
          <button className="icon-btn" title="Dismiss" onClick={() => onDismiss(t.id)}>
            ✕
          </button>
        </div>
      ))}
    </div>
  )
}
