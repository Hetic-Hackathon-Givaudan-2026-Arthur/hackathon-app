# Lancer le backend

Depuis le Dev Container, exécuter :

```bash
cd backend && \
python -m pip install -r requirements.txt && \
cp -n .env.example .env && \
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Avant le lancement, renseigner `backend/.env` avec les accès Neon fournis dans
le chat. Le fichier `.env` est local et ne doit jamais être commité.

Routes :

- `GET /health`
- `WS /ws/analyse`

Le démarrage ouvre la connexion Neon PostgreSQL et initialise les tables
`outbox_events` et `processing_events`. Le client Python S3-compatible permet
d'envoyer un asset et de générer une URL de lecture temporaire :

```python
await asset_store.put_object("uploads/file.txt", "Hello World!")
url = await asset_store.get_signed_url("uploads/file.txt", expires_in=3600)
```

Les credentials AWS/S3 restent uniquement dans les variables d'environnement.
