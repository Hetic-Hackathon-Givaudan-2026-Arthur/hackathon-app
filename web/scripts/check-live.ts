import assert from 'node:assert/strict';
import { decodeDataAiMessage } from '../src/services/liveProtocol.ts';

assert.deepEqual(decodeDataAiMessage('{'), []);
assert.deepEqual(
  decodeDataAiMessage(JSON.stringify({ type: 'unknown', imageId: 'forest' })),
  [],
);
assert.deepEqual(
  decodeDataAiMessage(JSON.stringify({ type: 'image', imageId: 'forest' })),
  [{ type: 'images', imageIds: ['forest'] }],
);
assert.deepEqual(
  decodeDataAiMessage(
    JSON.stringify({
      type: 'keywords',
      keywords: [
        'Boisé',
        { text: 'Naturel', origin: 'client', sources: ['très naturel'] },
      ],
    }),
  ),
  [
    {
      type: 'keywords',
      keywords: [
        { text: 'Boisé', origin: 'interpretation', sources: [] },
        { text: 'Naturel', origin: 'client', sources: ['très naturel'] },
      ],
    },
  ],
);
assert.deepEqual(
  decodeDataAiMessage(
    JSON.stringify({
      type: 'suggestions',
      keywords: ['Frais'],
      imageIds: ['forest', 'forest', 'linen'],
      insight: 'Recherche de fraîcheur',
    }),
  ),
  [
    {
      type: 'keywords',
      keywords: [{ text: 'Frais', origin: 'interpretation', sources: [] }],
    },
    { type: 'images', imageIds: ['forest', 'linen'] },
    {
      type: 'insight',
      insight: {
        text: 'Recherche de fraîcheur',
        origin: 'interpretation',
        sources: [],
      },
    },
  ],
);
assert.deepEqual(
  decodeDataAiMessage(
    JSON.stringify({
      type: 'keywords',
      keywords: [{ text: 'Frais', origin: 'client' }],
    }),
  ),
  [
    {
      type: 'keywords',
      keywords: [{ text: 'Frais', origin: 'interpretation', sources: [] }],
    },
  ],
);
console.log(
  'OK : protocole Data/IA validé (images, mots-clés, insight, sécurité de provenance).',
);
