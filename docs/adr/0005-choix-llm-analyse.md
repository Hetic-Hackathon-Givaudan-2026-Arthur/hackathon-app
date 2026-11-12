# 0005. Choix du LLM pour l'analyse de transcription (LLM 1)

- Statut : proposée
- Date : 2026-11-12
- Décideurs : Ahmed

## Contexte

Le service reçoit des transcriptions en français via WebSocket. Un LLM (LLM 1) doit en extraire
une analyse structurée JSON `{ idea, details, visual_keywords }` avant de la transmettre immédiatement
au client. Cette extraction est sur le chemin critique : sa latence détermine le temps de réponse perçu.

Contraintes :
- Modèles hébergés localement via Ollama sur une machine sans GPU dédié (CPU ou GPU intégré)
- Transcriptions en français — la qualité de compréhension du français est un critère
- Sortie JSON stricte, schéma fixe, validée à 95 % minimum
- Temps de réponse médian visé : < 10 s par lot (acceptable pour V1)

## Méthode de décision

Un benchmark a été exécuté sur 5 modèles × 5 répétitions × 20 extraits de transcription français
(100 appels par modèle). Métriques mesurées :
- Latence médiane et p95 (ms)
- Débit tokens/s
- Taux de JSON valide (%)
- Taux de conformité au schéma (%)
- Score de qualité Jaccard sur les `details` (expected vs actual)

Script : `benchmark/run_benchmark.py` — Dataset : `benchmark/dataset.json`

## Options

### Option 1 — `qwen2.5:7b`
Modèle Qwen 2.5 7B d'Alibaba. Excellente compréhension du français et des langues asiatiques.
Avantages : bonne qualité de raisonnement, instructions following robuste, multilingual.
Inconvénients : plus lent que les modèles 1B sur CPU.

### Option 2 — `llama3.1:8b`
Modèle Llama 3.1 8B de Meta. Très bonne qualité générale en anglais et français.
Avantages : fort suivi d'instructions, JSON structuré fiable, large communauté.
Inconvénients : légèrement plus lourd que qwen2.5:7b.

### Option 3 — `qwen2.5:1.5b`
Modèle compact 1.5B. Très rapide sur CPU.
Avantages : latence faible, faible consommation mémoire.
Inconvénients : qualité de raisonnement réduite, risque de non-conformité schéma.

### Option 4 — `llama3.2:1b`
Modèle compact 1B de Meta.
Avantages : extrêmement rapide.
Inconvénients : qualité limitée pour des tâches d'extraction structurée complexe.

### Option 5 — `gemma3:1b`
Modèle compact 1B de Google.
Avantages : rapide, léger.
Inconvénients : performances en français moins documentées.

## Résultats du benchmark

> Tableau à compléter après exécution de `benchmark/run_benchmark.py`

| Modèle | Latence médiane (ms) | p95 (ms) | Tokens/s | JSON valid % | Schema OK % | Jaccard qualité |
|---|---|---|---|---|---|---|
| qwen2.5:7b | — | — | — | — | — | — |
| llama3.1:8b | — | — | — | — | — | — |
| qwen2.5:1.5b | — | — | — | — | — | — |
| llama3.2:1b | — | — | — | — | — | — |
| gemma3:1b | — | — | — | — | — | — |

Critères de seuil pour acceptation :
- JSON valid % ≥ 95
- Schema OK % ≥ 90
- Jaccard qualité ≥ 0.30

## Décision

> À compléter après analyse des résultats du benchmark.

Nous choisissons le modèle … parce que …

## Conséquences

- Positives : …
- Négatives, à accepter : …
- À revoir si : le Jaccard descend sous 0.25 sur un lot réel, ou si la latence p95 dépasse 30 s.

## Note sur le LLM 2 (pipeline visuel)

Le LLM 2 (construction de la requête visuelle pour le RAG) n'est pas soumis à cette ADR.
Un LoRA n'est pas encore entraîné ; le prompt engineering sera évalué dans un spike séparé.
L'adaptateur `lora_path` dans `benchmark/config.yaml` permet d'intégrer un futur LoRA sans
modifier le script de benchmark.
