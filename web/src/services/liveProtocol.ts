import type { Insight, Keyword, Origin } from '../types/moodboard';

/** Contrat WS avec l'équipe Data/IA. Les messages inconnus sont ignorés. */
export type DataAiEvent =
  | { type: 'keywords'; keywords: Keyword[] }
  | { type: 'images'; imageIds: string[] }
  | { type: 'insight'; insight: Insight };

type UnknownObject = Record<string, unknown>;

function record(value: unknown): UnknownObject | null {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    ? (value as UnknownObject)
    : null;
}

function provenance(value: UnknownObject): {
  origin: Origin;
  sources: string[];
} {
  const sources = Array.isArray(value.sources)
    ? value.sources
        .filter(
          (item): item is string =>
            typeof item === 'string' && item.trim().length > 0,
        )
        .slice(0, 12)
    : [];
  // Un élément ne peut être marqué « Vos mots » sans au moins une citation fournie.
  const origin: Origin =
    value.origin === 'client' && sources.length ? 'client' : 'interpretation';
  return { origin, sources };
}

function keywords(value: unknown): Keyword[] {
  if (!Array.isArray(value)) return [];
  return value.flatMap((item): Keyword[] => {
    if (typeof item === 'string' && item.trim()) {
      return [{ text: item.trim(), origin: 'interpretation', sources: [] }];
    }
    const entry = record(item);
    return entry && typeof entry.text === 'string' && entry.text.trim()
      ? [{ text: entry.text.trim(), ...provenance(entry) }]
      : [];
  });
}

function imageIds(value: unknown): string[] {
  const raw = Array.isArray(value)
    ? value
    : typeof value === 'string'
      ? [value]
      : [];
  return raw
    .filter(
      (id): id is string => typeof id === 'string' && id.trim().length > 0,
    )
    .slice(0, 30);
}

function insight(value: unknown): Insight | null {
  if (typeof value === 'string' && value.trim()) {
    return { text: value.trim(), origin: 'interpretation', sources: [] };
  }
  const entry = record(value);
  return entry && typeof entry.text === 'string' && entry.text.trim()
    ? { text: entry.text.trim(), ...provenance(entry) }
    : null;
}

/**
 * Messages entrants acceptés :
 * { type:'keywords', keywords:['Boisé', {text:'Naturel',origin:'client',sources:['...']}] }
 * { type:'image', imageId:'forest' }
 * { type:'images', imageIds:['forest','linen'] }
 * { type:'insight', text:'Recherche de fraîcheur' }
 * { type:'suggestions', keywords:[...], imageIds:[...], insight:'...' }
 */
export function decodeDataAiMessage(raw: string): DataAiEvent[] {
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return [];
  }
  const data = record(parsed);
  if (!data || typeof data.type !== 'string') return [];

  const events: DataAiEvent[] = [];
  if (data.type === 'keywords' || data.type === 'suggestions') {
    const list = keywords(data.keywords);
    if (list.length) events.push({ type: 'keywords', keywords: list });
  }
  if (
    data.type === 'image' ||
    data.type === 'images' ||
    data.type === 'suggestions'
  ) {
    const ids = imageIds(data.imageIds ?? data.imageId);
    if (ids.length)
      events.push({ type: 'images', imageIds: [...new Set(ids)] });
  }
  if (data.type === 'insight' || data.type === 'suggestions') {
    const value = insight(data.insight ?? data.text);
    if (value) events.push({ type: 'insight', insight: value });
  }
  return events;
}
