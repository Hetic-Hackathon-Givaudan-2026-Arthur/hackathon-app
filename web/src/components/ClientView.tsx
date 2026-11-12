import { imageById } from '../services/share'
import type { ShareSnapshot } from '../types/moodboard'
import { Icon } from './Icon'
import { OriginBadge } from './OriginBadge'

/** Vue client : ce qui est partagé dans la visio. Lecture seule, sans sources ni réglages. */
export function ClientView({ snapshot }: { snapshot: ShareSnapshot | null }) {
  const images = snapshot?.images ?? (snapshot?.imageIds ?? []).map(imageById).filter((image) => image !== undefined)

  return (
    <div className="client-page">
      <div className="client-inner">
        <header className="client-header">
          <div className="brand">
            <div className="brand-mark"><Icon name="sparkles" size={19} /></div>
            <div className="brand-name">Accordel<span>.</span></div>
          </div>
          {snapshot?.company && <span className="client-company">{snapshot.company}</span>}
        </header>

        {!snapshot ? (
          <section className="client-empty">
            <h1>Rien à afficher pour le moment</h1>
            <p>Dans l’outil, terminez la démo puis appuyez sur Partager : cet onglet se remplit alors tout seul.</p>
          </section>
        ) : (
          <>
            <h1 className="client-title">Ce que nous avons retenu ensemble</h1>

            <section aria-labelledby="c-values">
              <h2 id="c-values" className="client-h2">Grandes valeurs</h2>
              <ul className="client-chips">
                {snapshot.keywords.map((keyword) => (
                  <li key={keyword.text} className="client-chip">
                    <span>{keyword.text}</span>
                    <OriginBadge origin={keyword.origin} />
                  </li>
                ))}
              </ul>
            </section>

            <section aria-labelledby="c-ideas">
              <h2 id="c-ideas" className="client-h2">Grandes idées</h2>
              <ul className="client-ideas">
                {snapshot.insights.map((insight) => (
                  <li key={insight.text} className="client-idea">
                    <OriginBadge origin={insight.origin} />
                    <p>{insight.text}</p>
                  </li>
                ))}
              </ul>
            </section>

            <section aria-labelledby="c-board">
              <h2 id="c-board" className="client-h2">Moodboard</h2>
              <div className="client-board">
                {images.map((image) => (
                  <figure key={image.id} className="client-image">
                    <img src={image.src} alt={image.alt} draggable={false} />
                    <div className="image-shade" />
                    <span className="client-image-badge"><OriginBadge origin={image.origin} /></span>
                    <figcaption>
                      <span>{image.category}</span>
                      <strong>{image.title}</strong>
                    </figcaption>
                  </figure>
                ))}
              </div>
            </section>

            <footer className="client-legend">
              <span><OriginBadge origin="client" /> vous l’avez dit</span>
              <span><OriginBadge origin="interpretation" /> déduit de vos propos</span>
              <span className="client-ask">Dites-nous si quelque chose ne vous ressemble pas.</span>
            </footer>
          </>
        )}
      </div>
    </div>
  )
}
