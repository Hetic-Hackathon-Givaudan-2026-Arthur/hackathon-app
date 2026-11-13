import type { MoodboardImage, Origin } from '../types/moodboard';

/** URL de l'API REST, vide = même origine (proxy Vite en développement). */
const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '')
  .trim()
  .replace(/\/$/, '');

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function textOr(value: unknown, fallback: string): string {
  return typeof value === 'string' && value.trim() ? value.trim() : fallback;
}

/** GET /api/img/:id : accepte image/jpeg|png|webp ou JSON {id,url,title,category,...}. */
export async function fetchMoodboardImage(
  id: string,
  signal?: AbortSignal,
): Promise<MoodboardImage> {
  if (!id.trim()) throw new Error('Identifiant d’image manquant');
  const endpoint = `${API_BASE}/api/img/${encodeURIComponent(id)}`;
  const response = await fetch(endpoint, {
    method: 'GET',
    signal,
    headers: { Accept: 'application/json, image/*' },
  });
  if (!response.ok)
    throw new Error(`Image ${id} introuvable : HTTP ${response.status}`);

  const contentType = response.headers.get('content-type')?.toLowerCase() ?? '';
  // Si l'API renvoie directement l'image, on garde l'URL HTTP pour la vue client et l'export.
  if (contentType.startsWith('image/')) {
    return {
      id,
      src: endpoint,
      alt: `Inspiration ${id}`,
      title: id,
      category: 'Inspiration',
      origin: 'interpretation',
      sources: [],
    };
  }
  if (!contentType.includes('application/json')) {
    throw new Error(
      `Réponse inattendue pour l'image ${id} (${contentType || 'sans Content-Type'})`,
    );
  }
  const data: unknown = await response.json();
  if (!isRecord(data))
    throw new Error(`Réponse JSON invalide pour l'image ${id}`);
  const url = data.url ?? data.src;
  if (typeof url !== 'string' || !url.trim())
    throw new Error(`L'image ${id} n'a pas de champ url/src`);
  const resolved = new URL(url.trim(), new URL(endpoint, window.location.href));
  if (resolved.protocol !== 'http:' && resolved.protocol !== 'https:')
    throw new Error('Protocole d’image non autorisé');
  const sources = Array.isArray(data.sources)
    ? data.sources.filter((x): x is string => typeof x === 'string')
    : [];
  const origin: Origin =
    data.origin === 'client' && sources.length ? 'client' : 'interpretation';
  return {
    id,
    src: resolved.href,
    title: textOr(data.title, id),
    alt: textOr(data.alt, textOr(data.title, id)),
    category: textOr(data.category, 'Inspiration'),
    origin,
    sources,
  };
}
