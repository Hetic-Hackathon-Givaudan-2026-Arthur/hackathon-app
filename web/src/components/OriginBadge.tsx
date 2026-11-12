
import type { Origin } from '../types/moodboard'
import { ORIGIN_LABELS } from '../constants/origins'
import { Icon } from './Icon'

/** Étiquette d'origine : libellé + icône + style propres à chaque origine (jamais la couleur seule). */
export function OriginBadge({ origin }: { origin: Origin }) {
  return (
    <span className={`origin-badge origin-${origin}`}>
      <Icon
        name={origin === 'client' ? 'quote' : 'sparkles'}
        size={11}
        strokeWidth={2.1}
      />
      {ORIGIN_LABELS[origin]}
    </span>
  )
}
