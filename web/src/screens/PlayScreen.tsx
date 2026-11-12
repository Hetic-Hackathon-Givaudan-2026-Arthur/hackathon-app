import { useCallback, useEffect, useMemo, useState } from 'react'
import { buildSnapshot, encodeShareHash, shareUrl, writeSnapshot } from '../services/share'
import { exportClientPage } from '../services/exportClientPage'
import { Icon } from '../components/Icon'
import { MoodboardCard } from '../components/MoodboardCard'
import { useMoodboardDemo } from '../hooks/useMoodboardDemo'
import { useLiveMoodboard } from '../hooks/useLiveMoodboard'
import { OriginBadge } from '../components/OriginBadge'
import { SourceBubble } from '../components/SourceBubble'
import type { SourceTarget } from '../components/SourceBubble'
import { SECTOR_LABELS } from '../types/client'
import type { ClientDraft } from '../types/client'

interface PlayScreenProps {
  client: ClientDraft
  onBack: () => void
}

/** Écran de play : joué pendant le rendez-vous avec le client. */
export function PlayScreen({ client, onBack }: PlayScreenProps) {
  const [mode, setMode] = useState<'demo' | 'live'>('demo')
  const demo = useMoodboardDemo()
  const live = useLiveMoodboard()
  const board = mode === 'demo' ? demo : live

  const [bubble, setBubble] = useState<{ target: SourceTarget; anchor: DOMRect } | null>(null)

  /** Un seul élément ouvert à la fois ; un second clic sur le même élément referme la bulle. */
  function openSource(target: SourceTarget, element: HTMLElement) {
    setBubble((current) => (current?.target.id === target.id ? null : { target, anchor: element.getBoundingClientRect() }))
  }
  const closeBubble = useCallback(() => setBubble(null), [])

  /** Partage : ouvre un onglet « vue client » (valeurs, idées, moodboard) que le commercial partage dans sa visio. */
  const [shared, setShared] = useState(false)
  const [exportStatus, setExportStatus] = useState('')
  const {
    status, images, keywords, insight, insights,
    start, togglePause, finish, reopen, removeImage,
  } = board
  const currentStep = mode === 'demo' ? demo.currentStep : images.length
  const totalSteps = mode === 'demo' ? demo.totalSteps : 1
  const allSuggested = mode === 'demo' && demo.allSuggested

  const isRunning = status === 'running'
  const isIdle = status === 'idle'
  const isFinished = status === 'finished'
  const isPaused = status === 'paused'

  const snapshot = useMemo(
    () => buildSnapshot(client.company, keywords, insights, images),
    [client.company, keywords, insights, images],
  )

  // Une fois partagé, l'onglet client suit les retraits d'images faits par le commercial.
  useEffect(() => {
    if (shared) writeSnapshot(snapshot)
  }, [shared, snapshot])

  function share() {
    writeSnapshot(snapshot)
    setShared(true)
    window.open(shareUrl(mode === 'demo' ? encodeShareHash(client.crmId, currentStep, images.map((image) => image.id)) : '#client-live'), '_blank')
  }

  /** Exporte la page client telle qu'elle est (images retirées comprises) en fichier HTML autonome. */
  async function exportBrief() {
    setExportStatus('')
    try {
      const { fileName, outcome } = await exportClientPage(snapshot)
      setExportStatus(
        outcome === 'saved' ? `Brief enregistré : ${fileName}.`
        : outcome === 'requested' ? `Téléchargement demandé : ${fileName}.`
        : outcome === 'declined' ? 'Enregistrement annulé.'
        : 'Export impossible ici.',
      )
    } catch {
      setExportStatus('Export impossible ici.')
    }
  }

  /** Modifier : on reprend la démo actuelle sans rien effacer ; il faudra repartager après les changements. */
  function modify() {
    setShared(false)
    setBubble(null)
    setExportStatus('')
    reopen()
  }

  return (
    <div className="desktop-scene">
      <div className="ambient ambient-one" aria-hidden="true" />
      <div className="ambient ambient-two" aria-hidden="true" />
      <div className="ambient ambient-three" aria-hidden="true" />

      <main className="widget" aria-label="Moodboard en direct">
        <header className="widget-header">
          <div className="brand">
            <div className="brand-mark"><Icon name="sparkles" size={19} /></div>
            <div>
              <div className="brand-name">Accordel<span>.</span></div>
              <div className="brand-subtitle">Creative companion</div>
            </div>
          </div>
          <button type="button" className="back-button" onClick={onBack}>
            <Icon name="arrow-left" size={14} /> Préparation
          </button>
        </header>

        <div className="client-strip" aria-label="Client du rendez-vous">
          <div className="client-strip-main">
            <div className="client-strip-top">
              <strong>{client.company || 'Client sans nom'}</strong>
              {client.sector && <span className="client-sector">{SECTOR_LABELS[client.sector]}</span>}
            </div>
            <span>
              {[client.contactName, client.contactRole].filter(Boolean).join(' · ') || 'Interlocuteur non renseigné'}
            </span>
          </div>
        </div>

        <div className="widget-scroll">
          <div className="meeting-mode-switch" role="group" aria-label="Mode du rendez-vous">
            <button type="button" className={mode === 'demo' ? 'selected' : ''}
              aria-pressed={mode === 'demo'} disabled={!isIdle}
              onClick={() => setMode('demo')}>Démo simulée</button>
            <button type="button" className={mode === 'live' ? 'selected' : ''}
              aria-pressed={mode === 'live'} disabled={!isIdle}
              onClick={() => setMode('live')}>Direct · micro</button>
          </div>

          <section className={`listening-panel glass-inset ${isRunning ? 'is-running' : ''}`} aria-label={mode === 'live' ? 'Transcription et connexion Data IA' : 'État de la simulation'}>
            <div className="listening-top">
              <span className={`live-indicator ${isRunning ? 'active' : ''}`}>
                <span className="live-dot" />
                {isIdle && 'off'}
                {isRunning && (mode === 'demo' ? (allSuggested ? 'Séquence terminée' : 'Analyse simulée en cours') : live.listening ? 'Micro actif · écoute en cours' : 'Démarrage du micro…')}
                {isPaused && (mode === 'demo' ? 'Simulation en pause' : 'Micro en pause')}
                {isFinished && 'Moodboard finalisé'}
              </span>
              <div className={`sound-bars ${isRunning && (mode === 'demo' ? !allSuggested : live.listening) ? 'animated' : ''}`} aria-hidden="true">
                {[7, 14, 10, 20, 12, 17, 8, 13, 6].map((height, index) => (
                  <span key={index} style={{ height }} />
                ))}
              </div>
            </div>
            {insight.origin ? (
              <button
                type="button"
                className="insight-trigger"
                data-source-trigger
                onClick={(event) => openSource(
                  { id: 'insight', title: 'Intention détectée', origin: insight.origin!, sources: insight.sources },
                  event.currentTarget,
                )}
              >
                <OriginBadge origin={insight.origin} />
                <span className="insight" aria-live="polite">{insight.text}</span>
              </button>
            ) : (
              <p className="insight" aria-live="polite">{insight.text}</p>
            )}
            {mode === 'demo' ? (
              <div className="progress-track" role="progressbar" aria-label="Progression de la démo" aria-valuenow={currentStep} aria-valuemin={0} aria-valuemax={totalSteps}>
                <div style={{ width: `${(currentStep / totalSteps) * 100}%` }} />
              </div>
            ) : (
              <>
                <div className="transcript-paper" aria-live="polite" aria-label="Transcription en direct">
                  {live.transcript || live.interim ? (
                    <><span>{live.transcript}</span><span className="transcript-interim"> {live.interim}</span></>
                  ) : (
                    <span className="transcript-placeholder">Les paroles apparaîtront ici. Seuls les segments confirmés sont envoyés à l'IA.</span>
                  )}
                </div>
                <p className="ws-indicator" role="status">
                  <span className={`ws-dot ws-${live.socketState}`} />
                  {live.socketState === 'connected' && 'IA connectée · WebSocket actif'}
                  {live.socketState === 'connecting' && 'Connexion à l’IA…'}
                  {live.socketState === 'reconnecting' && 'IA déconnectée · reconnexion…'}
                  {live.socketState === 'disconnected' && 'IA déconnectée'}
                  {live.socketState === 'not-configured' && 'Transcription locale · renseigner VITE_DATA_AI_WS_URL pour envoyer à l’IA'}
                </p>
                {live.error && <p className="live-error" role="alert">{live.error}</p>}
              </>
            )}
          </section>

          <section className="keywords-section" aria-label="Intentions créatives détectées">
            <div className="section-heading">
              <span>UNIVERS DÉTECTÉ</span>
              <Icon name="sparkles" size={14} />
            </div>
            <div className="keywords">
              {keywords.length === 0 ? (
                <span className="keywords-placeholder">Les mots-clés de l’IA apparaîtront ici</span>
              ) : keywords.map((keyword) => (
                <button
                  key={keyword.text}
                  type="button"
                  className="keyword-chip"
                  data-source-trigger
                  onClick={(event) => openSource(
                    { id: `kw:${keyword.text}`, title: keyword.text, origin: keyword.origin, sources: keyword.sources },
                    event.currentTarget,
                  )}
                >
                  <span className="chip-text">{keyword.text}</span>
                  <OriginBadge origin={keyword.origin} />
                </button>
              ))}
            </div>
          </section>

          <section className="moodboard-section" aria-label="Images du moodboard">
            <div className="section-heading board-heading">
              <span>MOODBOARD</span>
              <span className="image-count"><Icon name="layers" size={14} /> {images.length} visuel{images.length > 1 ? 's' : ''}</span>
            </div>
            {images.length > 0 ? (
              <div className="moodboard-grid">
                {[...images].reverse().map((image) => (
                  <MoodboardCard key={image.id} image={image} onRemove={removeImage} onOpenSource={openSource} />
                ))}
              </div>
            ) : (
              <div className="empty-board">
                <div className="empty-icon"><Icon name="layers" size={28} /></div>
                <strong>{isIdle ? 'Votre toile est prête' : 'Recherche des premières inspirations...'}</strong>
              </div>
            )}
          </section>
        </div>

        <footer className="widget-footer">
          <div className="footer-actions">
            {isIdle ? (
              <button type="button" className="action-button primary" onClick={start}>
                <Icon name="play" size={17} /> {mode === 'live' ? 'Démarrer l’écoute' : 'Lancer la démo'}
              </button>
            ) : isFinished ? (
              <>
                {shared ? (
                  <button type="button" className="action-button primary" onClick={exportBrief}>
                    <Icon name="download" size={17} /> Exporter le brief
                  </button>
                ) : (
                  <button type="button" className="action-button primary" onClick={share}>
                    <Icon name="share" size={17} /> Partager
                  </button>
                )}
                <button type="button" className="action-button secondary" onClick={modify}>
                  <Icon name="edit" size={15} /> Modifier
                </button>
              </>
            ) : (
              <>
                <button type="button" className="action-button primary" onClick={togglePause}>
                  <Icon name={isRunning ? 'pause' : 'play'} size={17} /> {isRunning ? (mode === 'live' ? 'Couper le micro' : 'Pause') : 'Reprendre'}
                </button>
                <button type="button" className="action-button secondary" onClick={finish}>
                  <Icon name="stop" size={15} /> Terminer
                </button>
              </>
            )}
          </div>
          {isFinished && (
            <p className="footer-hint" role="status" style={{ visibility: shared ? 'visible' : 'hidden' }}>
              Onglet ouvert : partagez-le dans votre visio.{' '}
              <button type="button" className="link-button" onClick={share}>Rouvrir l’onglet</button>
              {exportStatus && <><br />{exportStatus}</>}
            </p>
          )}
        </footer>
      </main>
      {bubble && <SourceBubble target={bubble.target} anchor={bubble.anchor} onClose={closeBubble} />}
    </div>
  )
}

