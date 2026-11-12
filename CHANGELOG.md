# Changelog

## 2026-11-12

### BACKEND-003 — Migration complète vers le backend Python

- Suppression du dossier `api/` et de ses dépendances Node.
- Déplacement du stockage S3-compatible dans `backend/infrastructure/assets.py`.
- Remplacement de la file Redis par une file FIFO persistante dans Neon.
- Ajout de l'idempotence par `analysis_id`, de l'acquittement après livraison et
  de la reprise des tâches expirées.
- Ajout du worker visuel et de sa composition LLM 2, RAG et recherche d'images.
- Injection de Neon dans l'outbox et le processing log append-only.
- Ajout de tests unitaires pour le flush final, l'idempotence et le worker FIFO.
- Ajout de la documentation OpenAPI des messages WebSocket.
- Mise à jour du lancement Dev Container, du frontend et du lockfile.

### À faire après BACKEND-003

- Fournir l'adaptateur LLM réel et assembler le worker visuel au démarrage.
- Connecter un gestionnaire WebSocket concret à `OutboxDelivery`.
- Ajouter les implémentations RAG et recherche d'images utilisées en production.
- Ajouter les tests d'intégration WebSocket, Neon, S3 et reprises.
- Définir les migrations Neon versionnées au lieu de créer les tables au
  démarrage.

### BACKEND-002 — Connexion Neon et lancement groupé

- Ajout de la configuration Python par variables d'environnement.
- Ajout de la connexion Neon PostgreSQL asynchrone.
- Ajout de la persistance des événements outbox et du processing log.
- Ajout du client S3-compatible Python pour les assets et les URLs signées.
- Ajout de `backend/.env.example` sans secrets.
- Ajout de la commande groupée dans `docs/backend.md`.
- Les valeurs de connexion réelles ne sont pas stockées dans le dépôt.

### À faire après BACKEND-002

- Injecter `NeonStore` et `S3AssetStore` dans la composition complète de
  l'orchestrateur.
- Remplacer l'ancien adaptateur Redis par la file Neon durable.
- Ajouter le client LLM et le worker visuel FIFO.
- Ajouter les tests d'intégration Neon/S3 avec des variables d'environnement de
  test.

### Ajouté

- Route WebSocket `WS /ws/analyse`.
- Validation stricte des messages `transcript` avec `type`, `text`,
  `isFinal`, `sessionId` et `segmentId`.
- Conversion des messages validés en `IngestSegmentCommand`.
- Enregistrement de l'orchestrateur dans l'état de l'application via
  `configure_orchestrator`.
- Orchestrateur applicatif : constitution des lots, analyse LLM 1, livraison
  immédiate du texte, puis création de la tâche visuelle.
- Vidage d'un lot lorsque le seuil est atteint ou lorsque `isFinal` vaut
  `true`.
- Contrat WebSocket documenté dans `docs/websocket.md`.

### À faire

- Assembler réellement l'orchestrateur au démarrage de l'application avec les
  adaptateurs LLM, Neon, l'outbox et la livraison WebSocket.
- Remplacer l'implémentation Redis existante par l'accès Neon défini par les
  règles du projet.
- Implémenter le worker visuel FIFO, l'appel LLM 2, le RAG et la recherche
  d'images.
- Garantir la persistance durable, l'idempotence et l'acquittement des tâches
  visuelles dans Neon.
- Implémenter le journal append-only des événements et les reprises avec
  politique de retry.
- Finaliser la livraison visuelle avec trame de contrôle JSON et trames
  binaires corrélées par `session_id` et `analysis_id`.
- Ajouter les tests d'intégration des contrats WebSocket, de Neon, de S3 et de
  la reprise des tâches.
- Documenter les événements et les contrats de sortie dans `openapi.yaml`.
