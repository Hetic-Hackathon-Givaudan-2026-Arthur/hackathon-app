import { renderToStaticMarkup } from 'react-dom/server';
import appCss from '../App.css?inline';
import baseCss from '../index.css?inline';
import { ClientView } from '../components/ClientView';
import type { ShareSnapshot } from '../types/moodboard';
import { saveTextFile } from './download';
import type { SaveOutcome } from './download';

/** La page envoyée au client, figée telle qu'elle s'affiche dans l'onglet de partage (après les retraits d'images du commercial). */
export function buildClientPageHtml(snapshot: ShareSnapshot): string {
  const body = renderToStaticMarkup(ClientView({ snapshot }));
  const title = `Brief${snapshot.company ? ` · ${snapshot.company}` : ''}`;
  return `<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${title.replace(/</g, '&lt;')}</title>
<style>${baseCss}\n${appCss}</style>
</head>
<body>
${body}
</body>
</html>
`;
}

export function clientPageFileName(company: string): string {
  const slug = company
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
  return `brief-${slug || 'client'}.html`;
}

export function exportClientPage(
  snapshot: ShareSnapshot,
): Promise<{ fileName: string; outcome: SaveOutcome }> {
  const fileName = clientPageFileName(snapshot.company);
  return saveTextFile(
    fileName,
    buildClientPageHtml(snapshot),
    'text/html;charset=utf-8',
  ).then((outcome) => ({ fileName, outcome }));
}
