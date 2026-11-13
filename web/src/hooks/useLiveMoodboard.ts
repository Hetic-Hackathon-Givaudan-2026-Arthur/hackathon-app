import { useCallback, useRef, useState } from 'react';
import { useSpeechRecognition } from './useSpeechRecognition';
import { demoEvents } from '../data/demoEvents';
import type {
  DemoStatus,
  Insight,
  InsightState,
  Keyword,
  MoodboardImage,
} from '../types/moodboard';
import type { SocketState } from '../services/dataAiSocket';

const WAITING: InsightState = {
  text: 'Parlez : les inspirations apparaîtront selon vos mots.',
  origin: null,
  sources: [],
};

const THEMES: { pattern: RegExp; ids: string[] }[] = [
  {
    pattern: /rose|jasmin|fleur|floral|parfum|lavande/i,
    ids: ['flowers', 'botanical'],
  },
  {
    pattern: /forêt|bois|nature|naturel|vert|végétal|rustique/i,
    ids: ['forest', 'botanical'],
  },
  {
    pattern: /frais|fraîcheur|léger|menthe|feuille/i,
    ids: ['botanical', 'ocean'],
  },
  {
    pattern: /mer|océan|plage|été|estival|soleil|vacances/i,
    ids: ['ocean', 'mineral'],
  },
  { pattern: /doux|douceur|coton|lin|sucré|crème/i, ids: ['linen', 'flowers'] },
  { pattern: /pierre|minéral|roche|terre|brut/i, ids: ['mineral', 'forest'] },
];

const IMAGE_NAMES: Record<string, string> = {
  flowers: 'Inspiration florale',
  forest: 'Forêt naturelle',
  botanical: 'Fraîcheur végétale',
  linen: 'Douceur et légèreté',
  ocean: 'Évasion marine',
  mineral: 'Univers minéral',
};

export function useLiveMoodboard() {
  const [status, setStatus] = useState<DemoStatus>('idle');
  const [images, setImages] = useState<MoodboardImage[]>([]);
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [insight, setInsight] = useState<InsightState>(WAITING);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [error, setError] = useState('');
  const [socketState] = useState<SocketState>('connected');
  const statusRef = useRef<DemoStatus>('idle');
  const seenRef = useRef(new Set<string>());
  const removedRef = useRef(new Set<string>());

  const onFinal = useCallback((text: string) => {
    if (statusRef.current !== 'running' || !text.trim()) return;
    const matching = THEMES.filter((theme) => theme.pattern.test(text));
    const ids = matching.length
      ? matching.flatMap((theme) => theme.ids)
      : ['botanical', 'flowers'];
    const uniqueIds = [...new Set(ids)];
    setImages((previous) => {
      const added = uniqueIds
        .filter((id) => !seenRef.current.has(id) && !removedRef.current.has(id))
        .map((id): MoodboardImage => {
          seenRef.current.add(id);
          const example = demoEvents.find(
            (event) => event.image.id === id,
          )?.image;
          return {
            id,
            src: `/images/${id}.jpg`,
            alt: example?.alt ?? IMAGE_NAMES[id] ?? id,
            title: example?.title ?? IMAGE_NAMES[id] ?? id,
            category: example?.category ?? 'Inspiration',
            origin: 'interpretation',
            sources: [text],
          };
        });
      return [...previous, ...added];
    });
    const words = matching.length
      ? [
          ...new Set(
            matching.flatMap((theme) =>
              theme.ids.map((id) => IMAGE_NAMES[id] ?? id),
            ),
          ),
        ]
      : ['Inspiration créative'];
    setKeywords((previous) => {
      const existing = new Set(previous.map((item) => item.text.toLowerCase()));
      return [
        ...previous,
        ...words
          .filter((word) => !existing.has(word.toLowerCase()))
          .map((word): Keyword => ({
            text: word,
            origin: 'interpretation',
            sources: [text],
          })),
      ];
    });
    const nextInsight: Insight = {
      text: ``,
      origin: 'interpretation',
      sources: [text],
    };
    setInsight(nextInsight);
    setInsights((previous) => [...previous, nextInsight]);
  }, []);

  const onFatal = useCallback(() => {
    if (statusRef.current === 'finished') return;
    statusRef.current = 'paused';
    setStatus('paused');
  }, []);
  const speech = useSpeechRecognition(onFinal, onFatal);

  const start = useCallback(() => {
    if (!speech.supported) {
      setError(
        'Reconnaissance vocale indisponible. Utilise Chrome sur localhost.',
      );
      return;
    }
    if (statusRef.current !== 'idle') return;
    speech.clear();
    setError('');
    setImages([]);
    setKeywords([]);
    setInsight(WAITING);
    setInsights([]);
    seenRef.current.clear();
    removedRef.current.clear();
    statusRef.current = 'running';
    if (speech.start()) setStatus('running');
    else statusRef.current = 'idle';
  }, [speech]);

  const togglePause = useCallback(() => {
    if (statusRef.current === 'running') {
      statusRef.current = 'paused';
      setStatus('paused');
      speech.stop();
    } else if (statusRef.current === 'paused' && speech.start()) {
      statusRef.current = 'running';
      setStatus('running');
    }
  }, [speech]);

  const finish = useCallback(() => {
    statusRef.current = 'finished';
    setStatus('finished');
    speech.stop();
  }, [speech]);

  const reopen = useCallback(() => {
    statusRef.current = 'paused';
    setStatus('paused');
  }, []);

  const removeImage = useCallback((id: string) => {
    removedRef.current.add(id);
    setImages((previous) => previous.filter((image) => image.id !== id));
  }, []);

  return {
    status,
    images,
    keywords,
    insight,
    insights,
    start,
    togglePause,
    finish,
    reopen,
    removeImage,
    transcript: speech.transcript,
    interim: speech.interim,
    listening: speech.listening,
    supported: speech.supported,
    error: error || speech.error,
    socketState,
    wsConfigured: true,
  };
}
