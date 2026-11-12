import type { Origin } from '../types/moodboard'
import { Icon } from './Icon'

export const ORIGIN_LABELS: Record<Origin, string> = {
  client: 'Vos mots',
  interpretation: 'Notre interprétation',
}

/** Étiquette d'origine : libellé + icône + style propres à chaque origine (jamais la couleur seule). */
export function OriginBadge({ origin }: { origin: Origin }) {
  return (
    <span className={`origin-badge origin-${origin}`}>
      <Icon name={origin === 'client' ? 'quote' : 'sparkles'} size={11} strokeWidth={2.1} />
      {ORIGIN_LABELS[origin]}
    </span>
  )
}
