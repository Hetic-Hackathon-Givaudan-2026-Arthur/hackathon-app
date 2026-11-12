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

## Résultat visuel

Le serveur envoie d'abord une trame JSON de contrôle :

```json
{
  "event": "visual_result",
  "session_id": "session-123",
  "analysis": {
    "analysis_id": "analysis_0042",
    "images": [
      {
        "image_id": "img_0081",
        "content_type": "image/webp",
        "byte_length": 48231
      }
    ]
  }
}
```

Les trames binaires suivantes contiennent les octets des images dans le même
ordre que le tableau `images`. Une trame binaire est envoyée par image et sa
taille doit correspondre à `byte_length`.
