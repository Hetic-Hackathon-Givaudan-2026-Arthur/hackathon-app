# AGENTS.md

Hackaton App est un projet développé avec Docker Compose et un Dev Container VS Code. Le projet utilise PostgreSQL 17 et un service de développement. Consulter `README.md` pour la présentation et l'architecture complète.

## Lancer

- Ouvrir `hackaton-app` dans VS Code, puis exécuter `Dev Containers: Reopen in Container`.
- Toutes les commandes npm et les outils de développement doivent être exécutés dans le Dev Container.
- `docker compose up -d` : démarrer les services `dev` et `db` depuis le terminal hôte si nécessaire.
- `docker compose ps` : vérifier l'état des conteneurs.
- `docker compose logs db --tail=100` : diagnostiquer les erreurs de PostgreSQL.
- Si les scripts existent dans `package.json`, utiliser `npm run dev` pour démarrer l'application, puis `npm run lint`, `npm run format:check` et `npm run build` avant de terminer une tâche.

## Règles

- Respecter les services `dev` et `db` définis dans `compose.yaml`.
- PostgreSQL utilise l'image `postgres:17`, la base `app` et les identifiants configurés dans `compose.yaml`.
- Les données PostgreSQL sont persistées dans `db/data/` ; les scripts de `db/init/` ne sont exécutés qu'à la première initialisation d'une base vide.
- Ne pas modifier `db/init/` en supposant que les changements s'appliqueront automatiquement à une base existante.
- Créer une branche par tâche depuis `develop`. Les pull requests ciblent `develop` et suivent `.github/pull_request_template.md`, si ce fichier existe.
- Consulter le ticket associé avec `gh issue view N`. Conserver les plans dans le ticket et les brouillons Markdown dans `.scratch/`, ignoré par Git.
- Toute modification de code, d'architecture, de dépendance, de contrat ou de configuration doit répondre à une requête explicite de l'utilisateur ou du ticket associé.
- Toute supposition fonctionnelle ou technique non vérifiable doit d'abord faire l'objet d'une requête de clarification avant d'être implémentée.
- Chaque itération doit être indiqué dans un fichier CHANGELOG qui indiquera la modification faite, lui attribuant un id
- Chaque fonction doit etre expliquée par des commentaires sur l'utilité de la fonction

## Backend Python

- Le backend est un service Python dont les entrées HTTP et WebSocket utilisent FastAPI.
- Respecter les responsabilités définies par l'architecture :
  - `entrypoints/` convertit les requêtes externes en commandes et ne contient aucune logique métier.
  - `application/` contient les cas d'usage et l'orchestration.
  - `domain/` contient les entités, identifiants, invariants et événements métier, sans dépendance technique.
  - `llm/` contient les prompts, schémas, services et adaptateurs propres à chaque modèle.
  - `pipelines/` contient les traitements texte et visuels indépendants.
  - `infrastructure/` contient les implémentations Neon, outbox et journal de traitement.
  - `composition/` assemble les implémentations concrètes et injecte les dépendances.
- Le résultat textuel doit être livré sans attendre la recherche visuelle. Le LLM 1 ne doit jamais attendre le LLM 2, le RAG ou les images.
- Les tâches visuelles doivent être durables dans Neon, corrélées par `session_id` et `analysis_id`, consommées en FIFO en V1 et acquittées après traitement durable.
- Préserver l'idempotence des segments, lots et tâches afin d'éviter les doublons lors des reprises.
- Définir des ports ciblés dans `application/ports/` et injecter les dépendances ; le domaine et l'application ne doivent pas dépendre de FastAPI, Neon ou d'un fournisseur LLM concret.
- Appliquer SOLID de manière pragmatique : responsabilité unique, ports ségrégés, inversion des dépendances, substitutions testables et extensions par implémentation de contrat.
- Appliquer YAGNI : ne pas ajouter de bus générique, plugin, DSL, microservice ou abstraction configurable sans besoin réel, mesuré et explicitement requis.
- Appliquer DRY : centraliser les contrats, validations, identifiants, règles métier et transformations partagés ; ne pas dupliquer une logique entre les entrées, pipelines et adaptateurs.
- Chaque fonction et méthode ajoutée ou modifiée doit comporter un commentaire ou une docstring concise expliquant son utilité et sa responsabilité. Ne pas commenter uniquement la syntaxe ou une action évidente.
- Documenter les événements, les contrats WebSocket et les changements de comportement dans `openapi.yaml` ou la documentation concernée.
- Toute nouvelle dépendance Python doit être ajoutée dans `backend/requirements.txt` après vérification des ADR et validation par une requête explicite.
- Pour tout accès à Neon, aux environnements ou aux secrets, demander les informations nécessaires dans le chat ; ne jamais deviner, rechercher ou ajouter des identifiants.

## Décisions

- Consulter `docs/adr/` avant d'ajouter une dépendance ou de modifier l'architecture, si ce répertoire existe.
- Respecter les ADR au statut « acceptée ».
- Si une décision acceptée doit changer, proposer un nouvel ADR et arrêter les modifications en attendant sa validation.
- Conserver PostgreSQL comme base de données tant qu'aucune décision d'architecture n'autorise son remplacement.

## À ne pas faire

- Ne jamais utiliser `git commit --no-verify` pour contourner les hooks Git.
- Ne pas ajouter `eslint-disable` uniquement pour masquer une erreur de qualité.
- Ne pas lancer `npm install` hors du Dev Container.
- Ne pas supprimer `db/data/` ni exécuter `docker compose down -v` sans autorisation explicite.
- Ne jamais commiter de mots de passe, tokens, clés API ou fichiers `.env` contenant des secrets.
- Ne pas ajouter de fichiers de suivi de session comme `TASKS.md` à la racine : utiliser les tickets GitHub et `.scratch/`.
