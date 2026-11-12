import type { MoodboardEvent } from '../types/moodboard';

/**
 * Données de la démo : un seul fichier.
 *
 * Source du scénario : BRIEF_VibeCoding.md, section 5 (appel fictif « Laiterie du Val »,
 * marque et personnes fictives). Seules les répliques du client (Julien) sont reprises,
 * telles quelles, mot pour mot.
 *
 * Règle : un élément « client » (Vos mots) reprend une expression que le client a dite ;
 * tout le reste est « interpretation » (Notre interprétation). Chaque source doit exister
 * mot pour mot dans `clientTranscript` : voir src/data/validateDemo.ts
 * et `npm run check:demo` (lancé avant chaque build).
 */
export const clientTranscript: string[] = [
  "On prépare un nouveau yaourt pour l'été prochain. Ma direction veut quelque chose qui donne un goût d'été, vraiment estival.",
  "Frais, léger, qui donne envie. Pas trop sucré. Plutôt pour des trentenaires qui font attention à ce qu'ils mangent.",
  "Milieu de gamme, mais avec de la personnalité. L'an dernier, on a essayé quelque chose de très fruité, ça n'a pas marché.",
  "En mars, en France d'abord. Et il faut que ça fasse naturel, un côté un peu boisé, rustique, mais pas trop.",
];

const S_NATUREL =
  'il faut que ça fasse naturel, un côté un peu boisé, rustique, mais pas trop';
const S_FRAIS = 'Frais, léger, qui donne envie';
const S_SUCRE = 'Frais, léger, qui donne envie. Pas trop sucré';
const S_ETE = "un goût d'été, vraiment estival";
const S_PERSO = 'mais avec de la personnalité';

/** Scénario fictif : six visuels locaux arrivent comme s'ils venaient d'une API. */
export const demoEvents: MoodboardEvent[] = [
  {
    image: {
      id: 'forest',
      src: '/images/forest.jpg',
      alt: 'Rayons de soleil dans une forêt verdoyante et brumeuse',
      title: 'Forêt à l’aube',
      category: 'Nature',
      origin: 'interpretation',
      sources: ['naturel, un côté un peu boisé, rustique'],
    },
    keywords: [
      {
        text: 'Naturel',
        origin: 'client',
        sources: ['il faut que ça fasse naturel'],
      },
      {
        text: 'Boisé',
        origin: 'client',
        sources: ['un côté un peu boisé, rustique'],
      },
    ],
    insight: {
      text: 'Le client veut un côté naturel, un peu boisé et rustique.',
      origin: 'interpretation',
      sources: [S_NATUREL],
    },
  },
  {
    image: {
      id: 'botanical',
      src: '/images/botanical.jpg',
      alt: 'Feuilles vertes couvertes de fines gouttelettes',
      title: 'Rosée végétale',
      category: 'Fraîcheur',
      origin: 'interpretation',
      sources: [S_FRAIS],
    },
    keywords: [
      { text: 'Frais', origin: 'client', sources: [S_FRAIS] },
      { text: 'Léger', origin: 'client', sources: [S_FRAIS] },
    ],
    insight: {
      text: 'Le client décrit un yaourt frais, léger, qui donne envie.',
      origin: 'interpretation',
      sources: [S_FRAIS],
    },
  },
  {
    image: {
      id: 'linen',
      src: '/images/linen.jpg',
      alt: 'Voile de lin ivoire traversé par une lumière douce',
      title: 'Lumière douce',
      category: 'Sensations',
      origin: 'interpretation',
      sources: [S_SUCRE],
    },
    keywords: [
      { text: 'Pas trop sucré', origin: 'client', sources: ['Pas trop sucré'] },
      { text: 'Douceur', origin: 'interpretation', sources: [S_SUCRE] },
    ],
    insight: {
      text: 'Le client veut du léger, pas trop sucré.',
      origin: 'interpretation',
      sources: [S_SUCRE],
    },
  },
  {
    image: {
      id: 'ocean',
      src: '/images/ocean.jpg',
      alt: 'Vagues turquoise baignées de soleil',
      title: 'Souffle marin',
      category: 'Énergie',
      origin: 'interpretation',
      sources: [S_ETE],
    },
    keywords: [
      { text: 'Estival', origin: 'client', sources: ['vraiment estival'] },
      { text: 'Énergie', origin: 'interpretation', sources: [S_FRAIS, S_ETE] },
    ],
    insight: {
      text: 'Le client parle d’un goût d’été, vraiment estival.',
      origin: 'interpretation',
      sources: [S_ETE],
    },
  },
  {
    image: {
      id: 'mineral',
      src: '/images/mineral.jpg',
      alt: 'Pierres naturelles claires et bois flotté',
      title: 'Matières brutes',
      category: 'Textures',
      origin: 'interpretation',
      sources: ['un côté un peu boisé, rustique'],
    },
    keywords: [
      { text: 'Rustique', origin: 'client', sources: ['boisé, rustique'] },
      { text: 'Authenticité', origin: 'interpretation', sources: [S_NATUREL] },
    ],
    insight: {
      text: 'Les matières brutes prolongent le côté rustique demandé.',
      origin: 'interpretation',
      sources: ['un côté un peu boisé, rustique'],
    },
  },
  {
    image: {
      id: 'flowers',
      src: '/images/flowers.jpg',
      alt: 'Petites fleurs crème parmi un feuillage sauge',
      title: 'Botanique sensible',
      category: 'Botanique',
      origin: 'interpretation',
      sources: ['rustique, mais pas trop'],
    },
    keywords: [
      { text: 'Personnalité', origin: 'client', sources: [S_PERSO] },
      {
        text: 'Délicatesse',
        origin: 'interpretation',
        sources: ['mais pas trop'],
      },
    ],
    insight: {
      text: 'Le « mais pas trop » appelle une touche subtile.',
      origin: 'interpretation',
      sources: ['rustique, mais pas trop'],
    },
  },
];
