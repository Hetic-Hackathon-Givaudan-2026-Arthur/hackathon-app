# Accordel (prototype)

Prototype React + Vite + TypeScript. Données fictives uniquement.

## Lancer

```bash
npm install
npm run dev        # serveur local
npm run build      # contrôle des sources de la démo, vérification TypeScript, build
```

## Parcours

1. **Préparation** : liste des rendez-vous (CRM simulé, `src/services/crm.ts`), choix d'un client, accord d'écoute.
2. **Play** : démo rejouée (`src/data/demoEvents.ts`) ; chaque mot-clé, intention et image porte une origine (« Vos mots » ou « Notre interprétation ») et des phrases sources. Clic sur un élément : bulle de source.
3. **Terminer**, puis **Partager** (ouvre l'onglet « vue client », `#client-...`) et **Exporter le brief** (page client en fichier HTML) ; **Modifier** rouvre la démo en cours.

## Points d'attention

- `npm run check:demo` échoue si une étiquette « Vos mots » n'est pas adossée à une phrase du client présente mot pour mot dans la transcription.
- Le CRM, le partage d'écran et l'écoute sont simulés ; aucun backend.

## Transcription vocale & Data/IA (nouveau)

Deux modes sont disponibles dans l'écran de rendez-vous : `Démo simulée` et `Direct · micro`.
Le mode direct reprend la Web Speech API de Chrome et envoie les segments confirmés par WebSocket.
Les images reçues sont chargées depuis `GET /api/img/:id`.

**Configuration, formats WS et API, limitations Teams :** voir `../INTEGRATION-TRANSCRIPTION.md`.
