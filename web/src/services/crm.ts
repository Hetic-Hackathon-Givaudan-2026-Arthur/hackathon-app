import type { CrmClient } from '../types/client';

/**
 * Source CRM simulée (données fictives uniquement, RGPD).
 * Point de branchement : remplacer le corps de `searchCrmClients` par un appel
 * MCP ou API (même signature). L'interface ne dépend que du type `CrmClient`.
 */
const FAKE_CRM: CrmClient[] = [
  {
    id: 'crm-001',
    company: 'Atelier Verdelune',
    contactName: 'Camille Roussel',
    contactRole: 'Cheffe de produit',
    region: 'Occitanie',
    scale: 'regional',
    sector: 'beaute',
    meetingTime: '10:00',
    subject: 'Premier brief pour une nouvelle gamme de soins',
  },
  {
    id: 'crm-002',
    company: 'Brume & Compagnie',
    contactName: 'Malik Ferrand',
    contactRole: 'Responsable marketing',
    region: 'Bretagne',
    scale: 'local',
    sector: 'parfum',
    meetingTime: '11:30',
    subject: 'Refonte d’une bougie parfumée de la collection d’hiver',
  },
  {
    id: 'crm-003',
    company: 'Sève Infusions',
    contactName: 'Inès Deltour',
    contactRole: 'Cheffe de produit',
    region: 'Auvergne-Rhône-Alpes',
    scale: 'regional',
    sector: 'gout',
    meetingTime: '14:00',
    subject: 'Nouvelle infusion glacée pour l’été',
  },
  {
    id: 'crm-004',
    company: 'Marée Douce',
    contactName: 'Paul Garnier',
    contactRole: 'Responsable marketing',
    region: 'Normandie',
    scale: 'local',
    sector: 'gout',
    meetingTime: '16:15',
    subject: 'Gamme de biscuits salés, repositionnement',
  },
];

/** Lecture synchrone d'une fiche par identifiant (la vue client retrouve ainsi le nom de la marque). */
export function getCrmClient(id: string): CrmClient | undefined {
  return FAKE_CRM.find((client) => client.id === id);
}

/** Rendez-vous du jour. Remplacer par l'appel MCP ou API du CRM (même signature). */
export async function fetchTodaysMeetings(): Promise<CrmClient[]> {
  await new Promise((resolve) => window.setTimeout(resolve, 700));
  return FAKE_CRM;
}
