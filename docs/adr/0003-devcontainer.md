# 0003. Utiliser un Dev Container pour le développement

- **Statut :** acceptée
- **Date :** 2026-11-05
- **Décideurs :** équipe Tech Lead

## Contexte

Plusieurs personnes travaillent sur le projet. Nous devons éviter les différences d'environnement et les problèmes de versions entre les machines.

## Options

1. **Installation locale :** simple, mais risque de différences de configuration risque de cas ' ça fonctinne sur ma machine...'
2. **Dev Container :** environnement identique pour tous, mais dependant de Docker

## Décision

Nous utilisons un Dev Container avec Node.js 24 pour garantir un environnement de développement commun et faciliter l'arrivée de nouveaux membres.

## Conséquences

- **Positives :** installation simplifiée, mêmes versions et moins de problèmes de compatibilité.
- **Négatives :** nécessite Docker et consomme des ressources.
- **À revoir si :** le conteneur devient trop lourd ou ralentit le développement.
