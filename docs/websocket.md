# Contrat WebSocket

## Réception d'un segment

Connexion :

```text
/ws/{session_id}
```

Le client envoie un objet JSON contenant exactement :

```json
{
  "segment_id": "segment_001",
  "text": "Transcription du segment"
}
```

`segment_id` et `text` sont obligatoires et ne peuvent pas être vides.
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
