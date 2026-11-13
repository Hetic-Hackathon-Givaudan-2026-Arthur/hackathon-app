/** Contrat utilisé par l'interface, indépendant du fournisseur Data/IA. */

/** Origine visible d'un élément : « Vos mots » (client) ou « Notre interprétation » (interpretation). */
export type Origin = 'client' | 'interpretation';

/** Provenance d'un élément. `sources` = phrases du client, mot pour mot (voir src/data/validateDemo.ts). */
export interface Provenance {
  origin: Origin;
  sources: string[];
}

export interface MoodboardImage extends Provenance {
  id: string;
  src: string;
  alt: string;
  title: string;
  category: string;
}

export interface Keyword extends Provenance {
  text: string;
}

/** Intention détectée, affichée dans le panneau d'écoute. */
export interface Insight extends Provenance {
  text: string;
}

/** État affiché de l'intention : sans origine tant qu'il s'agit d'un texte d'attente. */
export interface InsightState {
  text: string;
  origin: Origin | null;
  sources: string[];
}

export interface MoodboardEvent {
  image: MoodboardImage;
  keywords: Keyword[];
  insight: Insight;
}

/** Ce que le client voit dans l'onglet partagé : valeurs, idées et moodboard, rien d'autre. */
export interface ShareSnapshot {
  company: string;
  keywords: Keyword[];
  insights: Insight[];
  imageIds: string[];
  /** Les visuels reçus en direct ne figurent pas dans les assets de la démo. */
  images?: MoodboardImage[];
  updatedAt: number;
}

export type DemoStatus = 'idle' | 'running' | 'paused' | 'finished';
