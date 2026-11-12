# Contrat WebSocket

## Réception d'un segment

Connexion :

```text
/ws/analyse
```

Le client envoie un objet JSON contenant exactement :

```json
{
  "type": "transcript",
  "segmentId": "segment-001",
  "text": "Transcription du segment",
  "isFinal": true,
  "sessionId": "session-123",
  "segmentId": "segment-001"
}
```

`type` doit être `transcript`. `text`, `sessionId` et `segmentId` sont
obligatoires et ne peuvent pas être vides. `isFinal` est obligatoire.
Les champs supplémentaires sont refusés.

## Erreurs de réception

Pour un JSON invalide, le serveur envoie :

```json
{
  "event": "error",
  "code": "invalid_json",
  "message": "..."
}
```

Pour un segment qui ne respecte pas le contrat, le serveur envoie :

```json
{
  "event": "error",
  "code": "invalid_segment",
  "message": "..."
}
```

La connexion reste ouverte afin de permettre l'envoi d'un segment valide.
