/** Domaine large du rendez-vous. Il cadre les catégories à remplir ; il ne choisit jamais le contenu des interprétations (BRIEF v3, sélecteur de secteur). */
export type Sector = 'gout' | 'parfum' | 'beaute';

export type ClientScale = 'local' | 'regional' | 'international';

/** Fiche client utilisée par l'écran de préparation puis l'écran de play. */
export interface ClientDraft {
  company: string;
  contactName: string;
  contactRole: string;
  region: string;
  scale: ClientScale | '';
  sector: Sector | '';
  subject: string;
  /** Identifiant CRM si la fiche a été importée, sinon null (saisie manuelle). */
  crmId: string | null;
  consent: boolean;
}

/** Contrat renvoyé par le CRM, indépendant du fournisseur (MCP, API REST, export). Identité et contexte seulement, pas d'historique d'échanges. */
export interface CrmClient {
  id: string;
  company: string;
  contactName: string;
  contactRole: string;
  region: string;
  scale: ClientScale;
  sector: Sector;
  /** Heure du rendez-vous et objet, tels que saisis dans le CRM. */
  meetingTime: string;
  subject: string;
}

export const SECTOR_LABELS: Record<Sector, string> = {
  gout: 'Goût & bien-être',
  parfum: 'Parfum',
  beaute: 'Beauté',
};

export const SCALE_LABELS: Record<ClientScale, string> = {
  local: 'Local',
  regional: 'Régional',
  international: 'International',
};

export const emptyDraft: ClientDraft = {
  company: '',
  contactName: '',
  contactRole: '',
  region: '',
  scale: '',
  sector: '',
  subject: '',
  crmId: null,
  consent: false,
};
