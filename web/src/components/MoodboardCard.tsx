import type { MoodboardImage } from '../types/moodboard'
import type { SourceTarget } from './SourceBubble'
import { Icon } from './Icon'
import { OriginBadge } from './OriginBadge'

interface MoodboardCardProps {
  image: MoodboardImage
  onRemove: (id: string) => void
  onOpenSource: (target: SourceTarget, anchor: HTMLElement) => void
}

export function MoodboardCard({ image, onRemove, onOpenSource }: MoodboardCardProps) {
  const target: SourceTarget = { id: `img:${image.id}`, title: image.title, origin: image.origin, sources: image.sources }

  return (
    <article className="image-card" data-source-trigger onClick={(event) => onOpenSource(target, event.currentTarget)}>
      <img src={image.src} alt={image.alt} loading="eager" draggable={false} />
      <div className="image-shade" />
      <button
        className="origin-trigger"
        type="button"
        data-source-trigger
        aria-label={`Voir l’origine de ${image.title}`}
        onClick={(event) => {
          event.stopPropagation()
          onOpenSource(target, event.currentTarget.closest('article') as HTMLElement)
        }}
      >
        <OriginBadge origin={image.origin} />
      </button>
      <button
        className="image-remove"
        type="button"
        aria-label={`Retirer ${image.title} du moodboard`}
        title="Retirer cette image"
        onClick={(event) => {
          event.stopPropagation()
          onRemove(image.id)
        }}
      >
        <Icon name="x" size={15} />
      </button>
      <div className="image-caption">
        <span>{image.category}</span>
        <strong>{image.title}</strong>
      </div>
    </article>
  )
}
