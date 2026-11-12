import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import type { Origin } from '../types/moodboard'
import { OriginBadge } from './OriginBadge'

export interface SourceTarget {
  id: string
  title: string
  origin: Origin
  sources: string[]
}

interface SourceBubbleProps {
  target: SourceTarget
  anchor: DOMRect
  onClose: () => void
}

/** Bulle de provenance : un seul élément ouvert à la fois, fermée au clic extérieur, à Échap ou au défilement. */
export function SourceBubble({ target, anchor, onClose }: SourceBubbleProps) {
  const ref = useRef<HTMLDivElement>(null)
  const [pos, setPos] = useState<{ top: number; left: number } | null>(null)

  useLayoutEffect(() => {
    const el = ref.current
    if (!el) return
    const { offsetWidth: w, offsetHeight: h } = el
    const left = Math.min(Math.max(8, anchor.left), window.innerWidth - w - 8)
    let top = anchor.bottom + 8
    if (top + h > window.innerHeight - 8) top = Math.max(8, anchor.top - h - 8)
    setPos({ top, left })
  }, [anchor, target.id])

  useEffect(() => {
    function onPointerDown(event: PointerEvent) {
      const node = event.target as Element | null
      if (ref.current?.contains(node)) return
      if (node?.closest('[data-source-trigger]')) return // le déclencheur gère lui-même l'ouverture et la fermeture
      onClose()
    }
    function onKey(event: KeyboardEvent) {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('pointerdown', onPointerDown)
    document.addEventListener('keydown', onKey)
    window.addEventListener('scroll', onClose, true)
    window.addEventListener('resize', onClose)
    return () => {
      document.removeEventListener('pointerdown', onPointerDown)
      document.removeEventListener('keydown', onKey)
      window.removeEventListener('scroll', onClose, true)
      window.removeEventListener('resize', onClose)
    }
  }, [onClose])

  return createPortal(
    <div
      ref={ref}
      className="source-bubble"
      role="dialog"
      aria-label={`${target.title} : origine`}
      style={{ top: pos?.top ?? 0, left: pos?.left ?? 0, visibility: pos ? 'visible' : 'hidden' }}
    >
      <div className="source-bubble-head">
        <OriginBadge origin={target.origin} />
        <strong>{target.title}</strong>
      </div>
      <p className="source-bubble-lead">
        {target.origin === 'client'
          ? 'Le client l’a dit ainsi :'
          : 'Déduit par l’outil à partir de ce que le client a dit :'}
      </p>
      {target.sources.length === 0 && <p className="source-bubble-empty">Aucune citation fournie par l’IA.</p>}
      <ul className="source-bubble-list">
        {target.sources.map((source) => (
          <li key={source}>« {source} »</li>
        ))}
      </ul>
    </div>,
    document.body,
  )
}
