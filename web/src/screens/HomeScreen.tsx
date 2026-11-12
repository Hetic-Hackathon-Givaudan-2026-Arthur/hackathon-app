import { useCallback, useEffect, useState } from 'react'
import { Icon } from '../components/Icon'
import { fetchTodaysMeetings } from '../services/crm'
import { SCALE_LABELS, SECTOR_LABELS } from '../types/client'
import type { ClientDraft, CrmClient } from '../types/client'

interface HomeScreenProps {
  draft: ClientDraft
  onChange: (draft: ClientDraft) => void
  onStart: () => void
}

type SyncState = 'loading' | 'ready' | 'error'

/** Écran de préparation : la fiche client vient du CRM, jamais saisie à la main. */
export function HomeScreen({ draft, onChange, onStart }: HomeScreenProps) {
  const [sync, setSync] = useState<SyncState>('loading')
  const [meetings, setMeetings] = useState<CrmClient[]>([])

  const load = useCallback(() => {
    setSync('loading')
    fetchTodaysMeetings().then(
      (list) => { setMeetings(list); setSync('ready') },
      () => setSync('error'),
    )
  }, [])

  useEffect(() => { load() }, [load])

  function select(client: CrmClient) {
    onChange({
      company: client.company,
      contactName: client.contactName,
      contactRole: client.contactRole,
      region: client.region,
      scale: client.scale,
      sector: client.sector,
      subject: client.subject,
      crmId: client.id,
      consent: false,
    })
  }

  const selected = draft.crmId !== null
  const canStart = selected && draft.consent

  const rows: [string, string][] = selected ? [
    ['Interlocuteur', [draft.contactName, draft.contactRole].filter(Boolean).join(' · ')],
    ['Région', draft.region],
    ['Type de client', draft.scale ? SCALE_LABELS[draft.scale] : ''],
    ['Secteur', draft.sector ? SECTOR_LABELS[draft.sector] : ''],
    ['Objet', draft.subject],
  ] : []

  return (
    <div className="desktop-scene">
      <div className="ambient ambient-one" aria-hidden="true" />
      <div className="ambient ambient-two" aria-hidden="true" />
      <div className="ambient ambient-three" aria-hidden="true" />

      <main className="widget" aria-label="Préparation du rendez-vous">
        <header className="widget-header">
          <div className="brand">
            <div className="brand-mark"><Icon name="sparkles" size={19} /></div>
            <div>
              <div className="brand-name">Accordel<span>.</span></div>
              <div className="brand-subtitle">Creative companion</div>
            </div>
          </div>
          <span className="demo-pill">PRÉPARATION</span>
        </header>

        <div className="widget-scroll">
          <section className="hero">
            <div className="hero-eyebrow">AGENDA</div>
            {/* Interface seule : la navigation entre les jours n'est pas encore branchée. */}
            <div className="day-nav">
              <button type="button" className="day-arrow" aria-label="Jour précédent"><Icon name="chevron-left" size={16} /></button>
              <h1>Aujourd’hui</h1>
              <button type="button" className="day-arrow" aria-label="Jour suivant"><Icon name="chevron-right" size={16} /></button>
            </div>
          </section>

          <section aria-label="Rendez-vous du CRM">
            <div className="section-heading">
              <span className="sync-label">
                <span className={`sync-dot ${sync}`} />
                {sync === 'loading' && 'SYNCHRONISATION DU CRM…'}
                {sync === 'ready' && 'CRM SYNCHRONISÉ · DONNÉES FICTIVES'}
                {sync === 'error' && 'CRM INJOIGNABLE'}
              </span>
              <button type="button" className="link-button" onClick={load} disabled={sync === 'loading'}>
                <Icon name="refresh" size={12} /> Actualiser
              </button>
            </div>

            {sync === 'loading' && (
              <div className="crm-loading" aria-live="polite"><span /><span /><span /></div>
            )}
            {sync === 'error' && (
              <p className="crm-empty">Impossible de joindre le CRM. Actualisez dans un instant.</p>
            )}
            {sync === 'ready' && (
              <ul className="crm-list meeting-list">
                {meetings.map((client) => (
                  <li key={client.id}>
                    <button type="button" aria-pressed={draft.crmId === client.id}
                      className={draft.crmId === client.id ? 'is-selected' : ''} onClick={() => select(client)}>
                      <span className="meeting-time">{client.meetingTime}</span>
                      <span className="crm-item-main">
                        <strong>{client.company}</strong>
                        <span>{client.contactName} · {client.contactRole}</span>
                      </span>
                      <span className="meeting-check" aria-hidden="true"><Icon name="check" size={13} /></span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>

          {selected && (
            <section className="fiche glass-inset" aria-label="Fiche client importée">
              <div className="fiche-head">
                <div className="crm-avatar big">{draft.company.slice(0, 1)}</div>
                <div className="fiche-title">
                  <strong>{draft.company}</strong>
                  <span><Icon name="database" size={11} /> Importée du CRM</span>
                </div>
              </div>
              <dl className="fiche-grid">
                {rows.map(([label, value]) => (
                  <div key={label} className="fiche-row">
                    <dt>{label}</dt>
                    <dd className={value ? '' : 'is-missing'}>{value || 'Non renseigné dans le CRM'}</dd>
                  </div>
                ))}
              </dl>

              <label className={`consent ${draft.consent ? 'is-on' : ''}`} htmlFor="f-consent">
                <input id="f-consent" type="checkbox" checked={draft.consent} onChange={(e) => onChange({ ...draft, consent: e.target.checked })} />
                <span className="consent-box" aria-hidden="true"><Icon name="check" size={13} /></span>
                <span>
                  <strong>Le client a donné son accord</strong>
                  <span>Pour l’écoute pendant le rendez-vous. Un indicateur reste visible à l’écran.</span>
                </span>
              </label>
            </section>
          )}
        </div>

        <footer className="widget-footer">
          <button type="button" className="action-button primary full" disabled={!canStart} onClick={onStart}>
            <Icon name="play" size={17} /> Démarrer le rendez-vous
          </button>
        </footer>
      </main>
    </div>
  )
}
