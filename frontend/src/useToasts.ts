import { useCallback, useState } from 'react'

const TOAST_MS = 6000

export interface Toast {
  id: string
  message: string
}

export type Notify = (message: string, opts?: { id?: string; sticky?: boolean }) => void

// id: dedupe key (same id never shown twice); sticky: stays until dismissed in code
export function useToasts() {
  const [toasts, setToasts] = useState<Toast[]>([])

  const dismiss = useCallback((id: string) => {
    setToasts((ts) => ts.filter((t) => t.id !== id))
  }, [])

  const notify: Notify = useCallback(
    (message, { id = crypto.randomUUID(), sticky = false } = {}) => {
      setToasts((ts) => (ts.some((t) => t.id === id) ? ts : [...ts, { id, message }]))
      if (!sticky) setTimeout(() => dismiss(id), TOAST_MS)
    },
    [dismiss],
  )

  return { toasts, notify, dismiss }
}
