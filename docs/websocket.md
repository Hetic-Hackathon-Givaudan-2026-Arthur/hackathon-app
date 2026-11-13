# Contrat WebSocket d'analyse

## Connexion unique

```text
/ws/analyse
```

Le client doit utiliser cette connexion unique pour envoyer les segments et
recevoir les résultats textuels et visuels. L'identifiant de session voyage
dans chaque message ; aucun endpoint WebSocket par session ou pour les images
n'est exposé.

## Envoi d'un segment confirmé

```json
{
  "session_id": "session_001",
  "segment_id": "segment_001",
  "text": "Transcription confirmée"
}
```

Les trois champs sont obligatoires et non vides. Les champs supplémentaires
sont refusés. Les segments sont regroupés par session ; cinq segments
déclenchent une analyse.

L'analyse utilise le service LLM 1 via Ollama. `LLM1_MODEL` permet de choisir
le modèle ; sa valeur par défaut est `qwen2.5:1.5b`.

## Erreurs

```json
{
  "event": "error",
  "code": "invalid_segment",
  "message": "..."
}
```

Un JSON invalide utilise le code `invalid_json`. La connexion reste ouverte
pour accepter un message valide.

## Résultat textuel

```json
{
  "event": "analysis_result",
  "session_id": "session_001",
  "analysis": {
    "analysis_id": "analysis_0042",
    "text": {
      "idea": "Identité visuelle naturelle et épurée",
      "details": ["Tons crème", "Vanille"]
    }
  }
}
```

## Résultat visuel

Le contrôle JSON est suivi d'une trame binaire par image, dans le même ordre.
`byte_length` est la taille exacte de la trame correspondante. Le navigateur
associe les octets à `image_id` et `analysis_id`.

```json
{
  "event": "visual_result",
  "session_id": "session_001",
  "analysis": {
    "analysis_id": "analysis_0042",
    "images": [
      {
        "image_id": "images/img_0081.webp",
        "content_type": "image/webp",
        "byte_length": 48231
      }
    ]
  }
}
```
