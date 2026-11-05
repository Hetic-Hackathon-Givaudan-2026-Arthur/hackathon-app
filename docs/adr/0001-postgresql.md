a remplir

# 0001. Utiliser PostgreSQL comme base de données

- Statut : acceptée
- Date : 2026-11-09
- Décideurs : l'équipe

## Contexte

Le produit stocke des questions et les réponses de l'IA. Le hackathon dure deux semaines : une seule base, déjà connue de l'équipe, disponible en conteneur.

## Options

1. PostgreSQL : connue de l'équipe, image officielle, types JSON intégrés. Un service de plus à lancer.
2. SQLite : aucun service. Pas d'accès concurrent depuis l'API et le notebook IA.
3. MariaDB : connue aussi. Aucun avantage sur PostgreSQL ici.

## Décision

Nous choisissons PostgreSQL, lancé par `compose.yaml`, parce que l'API et le notebook IA doivent lire la même base en même temps.

## Conséquences

- Positives : même base sur toutes les machines et en démo.
- Négatives, à accepter : un conteneur à démarrer avant l'API.
- À revoir si : l'hébergement impose un autre moteur.
