# ADR — Choix de React pour le frontend

**Statut :** Proposéee
**Date :** 2026-11-09

## Contexte

Nous développons un copilote IA pour accompagner les commerciaux avant et après leurs rendez-vous clients.

Nous avons besoin d'une interface interactive, rapide à développer et facile à faire évoluer, car les fonctionnalités métier ne sont pas encore totalement définies.

## Décision

Nous choisissons **React avec TypeScript et Vite** pour le frontend.

## Avantages

- **Maîtrise technique :** React est déjà maîtrisé par le développeur, ce qui réduit le temps d'apprentissage et accélère le développement.
- **Rapidité de prototypage :** Vite permet de développer et tester rapidement les interfaces pendant le hackathon.
- **Flexibilité :** les composants React peuvent être modifiés ou réutilisés facilement lorsque les besoins business évoluent.
- **Intégration IA :** le frontend peut communiquer avec le backend et les services Data/IA via des API, permettant de travailler indépendamment.

## Inconvénients

- **Choix techniques à gérer :** React ne fournit pas directement toutes les fonctionnalités, comme le routage ou la gestion avancée des données.
- **Risque de complexité :** une architecture trop élaborée pourrait ralentir le développement sans apporter de valeur au prototype.

## Conséquences

Nous privilégions une architecture simple, avec des composants réutilisables et peu de dépendances.

Les fonctionnalités seront développées progressivement, à mesure que les besoins métier seront validés.

La communication avec la partie Data/IA passera par des API afin de limiter les dépendances entre les développements.
