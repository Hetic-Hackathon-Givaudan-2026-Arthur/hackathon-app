import { decodeDataAiMessage } from './liveProtocol';
import type { DataAiEvent } from './liveProtocol';

export type SocketState =
  | 'not-configured'
  | 'connecting'
  | 'connected'
  | 'reconnecting'
  | 'disconnected';

export const DATA_AI_WS_URL = (
  import.meta.env.VITE_DATA_AI_WS_URL ?? ''
).trim();

interface SocketOptions {
  onEvent: (event: DataAiEvent) => void;
  onState: (state: SocketState) => void;
  onError: (message: string) => void;
}

/**
 * Session WebSocket Data/IA.
 *
 * - Envoie les transcriptions confirmées.
 * - Reçoit les suggestions de mots-clés et d'images.
 * - Se reconnecte automatiquement.
 * - Conserve jusqu'à 50 messages en attente.
 */
export class DataAiSocket {
  private readonly url: string;
  private readonly options: SocketOptions;

  private socket: WebSocket | null = null;
  private closed = false;
  private retries = 0;
  private retryTimer: number | undefined;
  private pending: string[] = [];

  constructor(url: string, options: SocketOptions) {
    this.url = url;
    this.options = options;
  }

  connect() {
    if (!this.url) {
      this.options.onState('not-configured');
      return;
    }

    if (
      this.closed ||
      this.socket?.readyState === WebSocket.OPEN ||
      this.socket?.readyState === WebSocket.CONNECTING
    ) {
      return;
    }

    this.options.onState(this.retries ? 'reconnecting' : 'connecting');

    try {
      const socket = new WebSocket(this.url);
      this.socket = socket;

      socket.onopen = () => {
        if (this.closed) return;

        this.retries = 0;
        this.options.onState('connected');

        for (const message of this.pending) {
          socket.send(message);
        }

        this.pending = [];
      };

      socket.onmessage = (event: MessageEvent) => {
        if (this.closed || typeof event.data !== 'string') return;

        for (const message of decodeDataAiMessage(event.data)) {
          this.options.onEvent(message);
        }
      };

      socket.onerror = () => {
        if (!this.closed) {
          this.options.onError(
            'Connexion WebSocket indisponible : vérifie l’URL et le serveur Data/IA.',
          );
        }
      };

      socket.onclose = () => {
        if (this.closed) return;

        this.socket = null;
        this.options.onState('reconnecting');

        const delay = Math.min(1000 * 2 ** Math.min(this.retries++, 4), 15000);

        this.retryTimer = window.setTimeout(() => this.connect(), delay);
      };
    } catch {
      this.socket = null;

      this.options.onError(
        'URL WebSocket invalide : renseigne VITE_DATA_AI_WS_URL.',
      );

      this.options.onState('disconnected');
    }
  }

  sendTranscript(text: string, sessionId: string) {
    if (this.closed || !this.url || !text.trim()) return;

    const data = JSON.stringify({
      type: 'transcript',
      text: text.trim(),
      isFinal: true,
      sessionId,
    });

    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(data);
    } else {
      // Conserve seulement les 50 derniers segments
      // pendant une interruption de connexion.
      this.pending.push(data);

      if (this.pending.length > 50) {
        this.pending.shift();
      }
    }
  }

  close() {
    this.closed = true;

    window.clearTimeout(this.retryTimer);

    this.pending = [];

    if (this.socket) {
      this.socket.onclose = null;
      this.socket.onmessage = null;
      this.socket.onerror = null;
      this.socket.onopen = null;

      this.socket.close();
    }

    this.socket = null;

    this.options.onState('disconnected');
  }
}
