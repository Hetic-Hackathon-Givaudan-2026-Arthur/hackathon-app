# ADR — Utilisation d'OpenAPI pour le contrat d'interface

**Statut :** Acceptée (si validée par l'équipe)  
**Date :** 2026-11-10

## Contexte

Notre projet de hackathon Givaudan vise à transformer l'enregistrement d'un rendez-vous entre un commercial et un client en un moodboard destiné aux équipes créatives.

Le frontend est développé en React avec TypeScript. Les traitements Data/IA sont pris en charge séparément en Python.

Nous devons définir comment le frontend communiquera avec le service qui réalisera les traitements IA. Les fonctionnalités et les formats d'échange détaillés ne sont pas encore finalisés.

## Options envisagées

### Option 1 — Documenter les échanges dans le README

Cette approche est simple et ne nécessite pas de fichier supplémentaire, mais les formats de requêtes et de réponses risquent d'être imprécis ou difficiles à maintenir.

### Option 2 — Utiliser un contrat OpenAPI

OpenAPI permet de décrire les routes HTTP, les paramètres et les réponses dans un format standardisé, indépendant de React ou de Python.

Cette approche facilite la coordination entre les développeurs, mais impose de maintenir le contrat à jour lorsque l'API évolue.

## Décision

Nous retenons l'utilisation d'un contrat OpenAPI versionné dans le dépôt.

Ce contrat est défini dans le fichier **[`openapi.yaml`](../../openapi.yaml)**, situé à la racine du projet.

Pour le moment, il décrit uniquement la route technique `GET /health`, qui permettra de vérifier la disponibilité du futur service.

Les routes métier liées à l'analyse des rendez-vous et à la génération de moodboards seront ajoutées après validation des besoins et des échanges avec l'équipe Data/IA.

## Conséquences

- Le frontend React et le service Data/IA disposeront d'un contrat commun pour leurs échanges HTTP.
- Les nouvelles routes devront être documentées dans `openapi.yaml`.
- Le contrat pourra évoluer sans imposer immédiatement un framework backend particulier.
- Nous acceptons le coût de maintenance du fichier pour limiter les incompréhensions entre les équipes.
