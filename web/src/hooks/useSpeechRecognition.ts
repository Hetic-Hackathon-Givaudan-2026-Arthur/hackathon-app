import { useCallback, useEffect, useRef, useState } from 'react';

/** Déclarations locales : SpeechRecognition n'est pas disponible dans toutes les lib.dom. */
interface RecognitionResult {
  isFinal: boolean;
  0: { transcript: string };
}
interface RecognitionEvent {
  results: ArrayLike<RecognitionResult>;
}
interface RecognitionErrorEvent {
  error: string;
}
interface BrowserRecognition {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onstart: (() => void) | null;
  onresult: ((event: RecognitionEvent) => void) | null;
  onerror: ((event: RecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
  abort(): void;
}
type RecognitionConstructor = new () => BrowserRecognition;

function recognitionConstructor(): RecognitionConstructor | null {
  const browser = window as Window & {
    SpeechRecognition?: RecognitionConstructor;
    webkitSpeechRecognition?: RecognitionConstructor;
  };
  return browser.SpeechRecognition ?? browser.webkitSpeechRecognition ?? null;
}

const ERRORS: Record<string, string> = {
  'not-allowed': 'Microphone refusé : autorise son utilisation dans Chrome.',
  'service-not-allowed': 'Service de reconnaissance vocale non autorisé.',
  'audio-capture': 'Aucun microphone accessible.',
  network: 'Le service de reconnaissance vocale est indisponible (réseau).',
  'no-speech': 'Aucune parole détectée.',
};

/** Transcription navigateur fr-FR : envoie seulement les nouveaux segments FINAL, jamais les interim. */
export function useSpeechRecognition(
  onFinal: (text: string) => void,
  onFatal?: () => void,
) {
  const onFinalRef = useRef(onFinal);
  const onFatalRef = useRef(onFatal);

  useEffect(() => {
    onFinalRef.current = onFinal;
    onFatalRef.current = onFatal;
  }, [onFinal, onFatal]);
  const recognitionRef = useRef<BrowserRecognition | null>(null);
  const requestedRef = useRef(false);
  const sessionBaseRef = useRef('');
  const transcriptRef = useRef('');
  const sentFinalRef = useRef(new Set<number>());
  const [transcript, setTranscript] = useState('');
  const [interim, setInterim] = useState('');
  const [listening, setListening] = useState(false);
  const [error, setError] = useState('');
  const [supported] = useState(() => recognitionConstructor() !== null);

  const stop = useCallback(() => {
    requestedRef.current = false;
    setListening(false);
    setInterim('');
    recognitionRef.current?.stop();
  }, []);

  const start = useCallback((): boolean => {
    const Constructor = recognitionConstructor();
    if (!Constructor) {
      setError(
        'Reconnaissance vocale non disponible. Utilise Chrome avec HTTPS ou localhost.',
      );
      return false;
    }
    if (!recognitionRef.current) {
      const recognition = new Constructor();
      recognition.lang = 'fr-FR';
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.onstart = () => {
        setListening(true);
        setError('');
      };
      recognition.onresult = (event) => {
        let confirmed = '';
        let provisional = '';
        for (let i = 0; i < event.results.length; i++) {
          const result = event.results[i];
          if (result.isFinal) {
            const segment = result[0].transcript.trim();
            if (segment) {
              confirmed += `${segment} `;
              if (!sentFinalRef.current.has(i)) {
                sentFinalRef.current.add(i);
                onFinalRef.current(segment);
              }
            }
          } else {
            provisional += result[0].transcript;
          }
        }
        transcriptRef.current = [sessionBaseRef.current, confirmed.trim()]
          .filter(Boolean)
          .join(' ');
        setTranscript(transcriptRef.current);
        setInterim(provisional.trim());
      };
      recognition.onerror = (event) => {
        setError(
          ERRORS[event.error] ?? `Reconnaissance vocale : ${event.error}`,
        );
        if (
          [
            'not-allowed',
            'service-not-allowed',
            'audio-capture',
            'network',
          ].includes(event.error)
        ) {
          requestedRef.current = false;
          setListening(false);
          onFatalRef.current?.();
        }
      };
      recognition.onend = () => {
        setListening(false);
        if (requestedRef.current) {
          // Certaines versions de Chrome terminent la reconnaissance régulièrement.
          // La reprise conserve le texte sans renvoyer les anciens résultats au WebSocket.
          sessionBaseRef.current = transcriptRef.current;
          sentFinalRef.current.clear();
          setInterim('');
          try {
            recognition.start();
          } catch {
            requestedRef.current = false;
            onFatalRef.current?.();
          }
        } else {
          setInterim('');
        }
      };
      recognitionRef.current = recognition;
    }
    if (requestedRef.current) return true;
    sessionBaseRef.current = transcriptRef.current;
    sentFinalRef.current.clear();
    requestedRef.current = true;
    setError('');
    try {
      recognitionRef.current.start();
      return true;
    } catch (reason) {
      requestedRef.current = false;
      setError(
        reason instanceof Error
          ? reason.message
          : 'Impossible de démarrer le microphone.',
      );
      return false;
    }
  }, []);

  const clear = useCallback(() => {
    requestedRef.current = false;
    recognitionRef.current?.abort();
    transcriptRef.current = '';
    sessionBaseRef.current = '';
    sentFinalRef.current.clear();
    setTranscript('');
    setInterim('');
    setListening(false);
    setError('');
  }, []);

  useEffect(
    () => () => {
      requestedRef.current = false;
      if (recognitionRef.current) {
        recognitionRef.current.onend = null;
        recognitionRef.current.onresult = null;
        recognitionRef.current.onerror = null;
        recognitionRef.current.onstart = null;
        recognitionRef.current.abort();
      }
    },
    [],
  );

  return {
    supported,
    listening,
    transcript,
    interim,
    error,
    start,
    stop,
    clear,
  };
}
