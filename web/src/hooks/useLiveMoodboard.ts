import { useCallback, useEffect, useRef, useState } from 'react';
import { useSpeechRecognition } from './useSpeechRecognition';
import { DATA_AI_WS_URL, DataAiSocket } from '../services/dataAiSocket';
import type { SocketState } from '../services/dataAiSocket';
import { fetchMoodboardImage } from '../services/imagesApi';
import type { DataAiEvent } from '../services/liveProtocol';
import type {
  DemoStatus,
  Insight,
  InsightState,
  Keyword,
  MoodboardImage,
} from '../types/moodboard';

const WAITING: InsightState = {
  text: 'Les inspirations apparaîtront au fil de la conversation.',
  origin: null,
  sources: [],
};

/** Le mode réel conserve le même modèle images/mots-clés que la démo. */
export function useLiveMoodboard() {
  const [status, setStatus] = useState<DemoStatus>('idle');
  const [images, setImages] = useState<MoodboardImage[]>([]);
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [insight, setInsight] = useState<InsightState>(WAITING);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [socketState, setSocketState] = useState<SocketState>(
    DATA_AI_WS_URL ? 'disconnected' : 'not-configured',
  );
  const [error, setError] = useState('');
  const socketRef = useRef<DataAiSocket | null>(null);
  const statusRef = useRef<DemoStatus>('idle');
  const sessionIdRef = useRef('');
  const discardedIdsRef = useRef(new Set<string>());
  const requestedIdsRef = useRef(new Set<string>());
  const fetchesRef = useRef(new Set<AbortController>());

  const onSpeechFinal = useCallback((text: string) => {
    if (statusRef.current === 'running')
      socketRef.current?.sendTranscript(text, sessionIdRef.current);
  }, []);
  const onSpeechFatal = useCallback(() => {
    if (statusRef.current === 'finished') return;
    statusRef.current = 'paused';
    setStatus('paused');
  }, []);
  const speech = useSpeechRecognition(onSpeechFinal, onSpeechFatal);

  const receiveImage = useCallback(async (id: string) => {
    if (requestedIdsRef.current.has(id) || discardedIdsRef.current.has(id))
      return;
    requestedIdsRef.current.add(id);
    const controller = new AbortController();
    fetchesRef.current.add(controller);
    try {
      const image = await fetchMoodboardImage(id, controller.signal);
      if (!controller.signal.aborted && !discardedIdsRef.current.has(id)) {
        setImages((previous) =>
          previous.some((old) => old.id === id)
            ? previous
            : [...previous, image],
        );
      }
    } catch (reason) {
      if (!controller.signal.aborted) {
        requestedIdsRef.current.delete(id);
        setError(
          reason instanceof Error
            ? reason.message
            : `Impossible de récupérer l’image ${id}`,
        );
      }
    } finally {
      fetchesRef.current.delete(controller);
    }
  }, []);

  const onDataAiEvent = useCallback(
    (event: DataAiEvent) => {
      if (statusRef.current === 'finished' || statusRef.current === 'idle')
        return;
      if (event.type === 'keywords') {
        setKeywords((previous) => {
          const seen = new Set(
            previous.map((word) => word.text.toLocaleLowerCase('fr')),
          );
          return [
            ...previous,
            ...event.keywords.filter((word) => {
              const key = word.text.toLocaleLowerCase('fr');
              if (seen.has(key)) return false;
              seen.add(key);
              return true;
            }),
          ];
        });
      } else if (event.type === 'images') {
        for (const id of event.imageIds) void receiveImage(id);
      } else if (event.type === 'insight') {
        setInsight(event.insight);
        setInsights((previous) => [...previous, event.insight]);
      }
    },
    [receiveImage],
  );

  const connect = useCallback(() => {
    if (socketRef.current || !DATA_AI_WS_URL) return;
    const socket = new DataAiSocket(DATA_AI_WS_URL, {
      onEvent: onDataAiEvent,
      onState: setSocketState,
      onError: setError,
    });
    socketRef.current = socket;
    socket.connect();
  }, [onDataAiEvent]);

  const start = useCallback(() => {
    if (!speech.supported) {
      setError(
        'La reconnaissance vocale n’est pas disponible ici. Ouvre Moodflow dans Chrome.',
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
    discardedIdsRef.current.clear();
    requestedIdsRef.current.clear();
    sessionIdRef.current =
      window.crypto?.randomUUID?.() ?? `meeting-${Date.now()}`;
    statusRef.current = 'running';
    // Le démarrage du microphone se fait directement depuis le clic utilisateur.
    if (speech.start()) {
      setStatus('running');
      connect();
    } else {
      statusRef.current = 'idle';
    }
  }, [speech, connect]);

  const togglePause = useCallback(() => {
    if (statusRef.current === 'running') {
      statusRef.current = 'paused';
      setStatus('paused');
      speech.stop();
    } else if (statusRef.current === 'paused') {
      if (speech.start()) {
        statusRef.current = 'running';
        setStatus('running');
        connect();
      }
    }
  }, [speech, connect]);

  const finish = useCallback(() => {
    statusRef.current = 'finished';
    setStatus('finished');
    speech.stop();
    socketRef.current?.close();
    socketRef.current = null;
    for (const controller of fetchesRef.current) controller.abort();
    fetchesRef.current.clear();
  }, [speech]);

  const reopen = useCallback(() => {
    statusRef.current = 'paused';
    setStatus('paused');
    // L'écoute repart seulement sur un clic explicite « Reprendre ».
  }, []);

  const removeImage = useCallback((id: string) => {
    discardedIdsRef.current.add(id);
    setImages((previous) => previous.filter((image) => image.id !== id));
  }, []);

  useEffect(
    () => () => {
      socketRef.current?.close();
      for (const controller of fetchesRef.current) controller.abort();
    },
    [],
  );

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
    wsConfigured: !!DATA_AI_WS_URL,
  };
}
