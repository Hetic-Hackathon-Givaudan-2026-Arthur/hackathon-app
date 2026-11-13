/**
 * Enregistre un fichier texte.
 * - Dans un artifact publié : capacité `downloads` (le viewer confirme l'enregistrement).
 * - Hors artifact (fichier ouvert en local) : téléchargement direct par le navigateur.
 */
export type SaveOutcome = 'saved' | 'requested' | 'declined' | 'failed';

type DownloadsApi = {
  save: (request: { filename: string; data: string }) => Promise<unknown>;
};
type ClaudeHost = { use?: (name: string) => Promise<DownloadsApi | null> };

export async function saveTextFile(
  filename: string,
  data: string,
  mime: string,
): Promise<SaveOutcome> {
  const host = (window as unknown as { claude?: ClaudeHost }).claude;
  const downloads = host?.use
    ? await host.use('downloads').catch(() => null)
    : null;

  if (downloads) {
    try {
      await downloads.save({ filename, data });
      return 'saved';
    } catch (error) {
      return (error as { code?: string } | null)?.code === 'declined'
        ? 'declined'
        : 'failed';
    }
  }

  try {
    const url = URL.createObjectURL(new Blob([data], { type: mime }));
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    return 'requested';
  } catch {
    return 'failed';
  }
}
