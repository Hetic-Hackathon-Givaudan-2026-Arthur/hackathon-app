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
