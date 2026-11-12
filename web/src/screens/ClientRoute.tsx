import { useEffect, useState } from 'react';
import { ClientView } from '../components/ClientView';
import { decodeShareHash, isShareKey, readSnapshot } from '../services/share';
import type { ShareSnapshot } from '../types/moodboard';

/** Onglet « vue client » (#client) : se met à jour quand le commercial modifie le moodboard. */
export function ClientRoute() {
  const [snapshot, setSnapshot] = useState<ShareSnapshot | null>(() =>
    window.location.hash === '#client-live'
      ? readSnapshot()
      : (decodeShareHash(window.location.hash) ?? readSnapshot()),
  );

  useEffect(() => {
    function onStorage(event: StorageEvent) {
      if (isShareKey(event.key)) setSnapshot(readSnapshot());
    }
    function onHash() {
      setSnapshot(
        window.location.hash === '#client-live'
          ? readSnapshot()
          : (decodeShareHash(window.location.hash) ?? readSnapshot()),
      );
    }
    window.addEventListener('storage', onStorage);
    window.addEventListener('hashchange', onHash);
    return () => {
      window.removeEventListener('storage', onStorage);
      window.removeEventListener('hashchange', onHash);
    };
  }, []);

  return <ClientView snapshot={snapshot} />;
}
