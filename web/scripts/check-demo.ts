// Échoue (code 1) si une étiquette « Vos mots » n'est pas adossée à une phrase du client.
// Lancé par `npm run check:demo` et avant `npm run build` (Node 22.6+ : --experimental-strip-types).
import { demoEvents, clientTranscript } from '../src/data/demoEvents.ts';
import { validateDemo } from '../src/data/validateDemo.ts';

const errors = validateDemo(demoEvents, clientTranscript);
if (errors.length > 0) {
  console.error(
    `Démo invalide (${errors.length} erreur${errors.length > 1 ? 's' : ''}) :`,
  );
  for (const error of errors) console.error(' - ' + error);
  process.exit(1);
}
const count = demoEvents.reduce((n, e) => n + 2 + e.keywords.length, 0);
console.log(
  `Démo valide : ${count} éléments, chacun avec origine et source dans la transcription.`,
);
