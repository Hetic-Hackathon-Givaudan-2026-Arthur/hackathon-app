import type { MoodboardEvent, Provenance } from '../types/moodboard';

/**
 * Contrôle de la règle d'origine. Renvoie la liste des erreurs (vide = valide).
 * - tout élément (image, mot-clé, intention) a une origine valide et au moins une source ;
 * - chaque source existe mot pour mot (casse comprise) dans la transcription du client ;
 * - un élément « client » (Vos mots) reprend une expression présente dans l'une de ses sources.
 */
export function validateDemo(
  events: MoodboardEvent[],
  transcript: string[],
): string[] {
  const errors: string[] = [];
  const text = transcript.join('\n');

  function check(
    kind: string,
    label: string,
    element: Provenance,
    reusedText: string,
  ) {
    const where = `${kind} « ${label} »`;
    if (element.origin !== 'client' && element.origin !== 'interpretation') {
      errors.push(`${where} : origine absente ou invalide.`);
      return;
    }
    if (!Array.isArray(element.sources) || element.sources.length === 0) {
      errors.push(`${where} : aucune phrase source.`);
      return;
    }
    for (const source of element.sources) {
      if (source.trim() === '' || !text.includes(source)) {
        errors.push(
          `${where} : la source « ${source} » n'est pas dans la transcription du client.`,
        );
      }
    }
    if (element.origin === 'client') {
      const needle = reusedText.toLowerCase();
      if (
        !element.sources.some((source) => source.toLowerCase().includes(needle))
      ) {
        errors.push(
          `${where} : étiqueté « Vos mots » mais « ${reusedText} » n'apparaît dans aucune de ses sources.`,
        );
      }
    }
  }

  for (const event of events) {
    check('Image', event.image.title, event.image, event.image.title);
    for (const keyword of event.keywords)
      check('Mot-clé', keyword.text, keyword, keyword.text);
    check('Intention', event.insight.text, event.insight, event.insight.text);
  }
  return errors;
}
