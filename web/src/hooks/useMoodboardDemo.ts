import { useEffect, useState } from 'react';
import { demoEvents } from '../data/demoEvents';
import type {
  DemoStatus,
  Insight,
  InsightState,
  Keyword,
  MoodboardImage,
} from '../types/moodboard';

/**
 * Simule un flux d'événements d'images.
 * Plus tard, remplacer uniquement cette source par WebSocket/SSE/API.
 * L'interface reste indépendante de la méthode de transport.
 */
export function useMoodboardDemo() {
  const [status, setStatus] = useState<DemoStatus>('idle');
  const [images, setImages] = useState<MoodboardImage[]>([]);
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [insight, setInsight] = useState<InsightState>({
    text: 'les inspi apparaitrons au fil du rdv',
    origin: null,
    sources: [],
  });
  const [insights, setInsights] = useState<Insight[]>([]);
  const [nextIndex, setNextIndex] = useState(0);

  useEffect(() => {
    if (status !== 'running' || nextIndex >= demoEvents.length) return;

    const timeout = window.setTimeout(
      () => {
        const event = demoEvents[nextIndex];
        if (!event) return;
        setImages((previous) => [...previous, event.image]);
        setKeywords((previous) => {
          const known = new Set(previous.map((keyword) => keyword.text));
          return [
            ...previous,
            ...event.keywords.filter((keyword) => !known.has(keyword.text)),
          ];
        });
        setInsight(event.insight);
        setInsights((previous) => [...previous, event.insight]);
        setNextIndex((previous) => previous + 1);
      },
      nextIndex === 0 ? 900 : 2300,
    );

    return () => window.clearTimeout(timeout);
  }, [status, nextIndex]);

  function start() {
    setStatus('running');
  }

  function togglePause() {
    setStatus((previous) => (previous === 'running' ? 'paused' : 'running'));
  }

  function finish() {
    setStatus('finished');
  }

  function removeImage(id: string) {
    setImages((previous) => previous.filter((image) => image.id !== id));
  }

  /** Rouvre la démo en cours pour la modifier : rien n'est effacé, la séance repasse en pause. */
  function reopen() {
    setStatus('paused');
  }

  return {
    status,
    images,
    keywords,
    insight,
    insights,
    currentStep: nextIndex,
    totalSteps: demoEvents.length,
    allSuggested: nextIndex === demoEvents.length,
    start,
    togglePause,
    finish,
    reopen,
    removeImage,
  };
}
