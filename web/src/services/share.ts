import { demoEvents } from '../data/demoEvents';
import { getCrmClient } from './crm';
import type {
  Insight,
  Keyword,
  MoodboardImage,
  ShareSnapshot,
} from '../types/moodboard';

/**
 * Partage vers l'onglet « vue client ».
 * 1) Le contenu voyage dans le fragment de l'URL (#client-<fiche>-<étapes>-<images>) : toutes les données
 *    de la démo sont dans l'application, le fragment dit seulement quelle fiche, combien d'étapes révélées
 *    et quelles images restent. Aucun texte libre, aucune donnée personnelle. Cela marche même quand les
 *    onglets ne partagent aucun stockage (cas d'un artifact publié).
 * 2) Quand le stockage est partagé, localStorage + événement `storage` mettent l'onglet à jour en direct.
 * Remplacer par un lien serveur quand un backend existera.
 */
const KEY = 'accordel:share';
export const CLIENT_HASH = '#client';

export function buildSnapshot(
  company: string,
  keywords: Keyword[],
  insights: Insight[],
  images: MoodboardImage[],
): ShareSnapshot {
  return {
    company,
    keywords,
    insights,
    imageIds: images.map((image) => image.id),
    images,
    updatedAt: Date.now(),
  };
}

export function writeSnapshot(snapshot: ShareSnapshot): boolean {
  try {
    window.localStorage.setItem(KEY, JSON.stringify(snapshot));
    return true;
  } catch {
    return false;
  }
}

export function readSnapshot(): ShareSnapshot | null {
  try {
    const raw = window.localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as ShareSnapshot) : null;
  } catch {
    return null;
  }
}

export function clearSnapshot() {
  try {
    window.localStorage.removeItem(KEY);
  } catch {
    /* rien à faire */
  }
}

export function isShareKey(key: string | null) {
  return key === KEY || key === null; // null : stockage vidé
}

export function isClientHash(hash: string) {
  return hash === CLIENT_HASH || hash.startsWith(CLIENT_HASH + '-');
}

export function shareUrl(hash: string) {
  return window.location.href.split('#')[0] + hash;
}

/** Fragment : #client-<id fiche>-<nombre d'étapes révélées>-<masque des images conservées, une par étape>. */
export function encodeShareHash(
  crmId: string | null,
  revealed: number,
  imageIds: string[],
): string {
  const mask = demoEvents
    .map((event) => (imageIds.includes(event.image.id) ? '1' : '0'))
    .join('');
  return `${CLIENT_HASH}-${crmId ?? 'none'}-${revealed}-${mask}`;
}

export function decodeShareHash(hash: string): ShareSnapshot | null {
  const match = /^#client-([a-z0-9-]+)-(\d+)-([01]+)$/.exec(hash);
  if (!match) return null;
  const [, crmId, revealedText, mask] = match;
  const events = demoEvents.slice(
    0,
    Math.min(Number(revealedText), demoEvents.length),
  );
  const seen = new Set<string>();
  const keywords: Keyword[] = [];
  for (const event of events) {
    for (const keyword of event.keywords) {
      if (!seen.has(keyword.text)) {
        seen.add(keyword.text);
        keywords.push(keyword);
      }
    }
  }
  return {
    company: getCrmClient(crmId)?.company ?? '',
    keywords,
    insights: events.map((event) => event.insight),
    imageIds: events
      .filter((_, index) => mask[index] === '1')
      .map((event) => event.image.id),
    updatedAt: Date.now(),
  };
}

/** Les images restent dans l'application : l'instantané ne garde que leurs identifiants. */
export function imageById(id: string): MoodboardImage | undefined {
  return demoEvents
    .map((event) => event.image)
    .find((image) => image.id === id);
}
