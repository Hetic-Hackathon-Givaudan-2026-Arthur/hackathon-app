# Benchmark LLM 1 — Analyse de transcription

Ce benchmark mesure la capacité des modèles LLM 8B (et variants) à extraire une analyse structurée JSON
depuis des transcriptions créatives en français, selon le schéma défini dans l'architecture technique.

## Schéma attendu

```json
{
  "idea": "Résumé de l'intention principale (string)",
  "details": ["point 1", "point 2"],
  "visual_keywords": ["mot1", "mot2"]
}
```

`visual_keywords` est interne (non transmis au client) et optionnel dans la V1.

## Prérequis

- Python 3.9+ (aucune dépendance externe)
- [Ollama](https://ollama.com) actif sur `http://localhost:11434`
- Modèles installés :
  ```
  ollama pull qwen2.5:7b
  ollama pull llama3.1:8b
  ollama pull qwen2.5:1.5b
  ollama pull llama3.2:1b
  ollama pull gemma3:1b
  ```

## Lancer le benchmark

Depuis la **racine du projet** :

```bash
python benchmark/run_benchmark.py
```

Avec un endpoint Ollama différent :

```bash
OLLAMA_BASE_URL=http://mon-serveur:11434 python benchmark/run_benchmark.py
```

Avec un fichier de config alternatif :

```bash
python benchmark/run_benchmark.py --config benchmark/config.yaml
```

## Résultats

Les résultats sont écrits dans `benchmark/results/benchmark_<timestamp>.json`.
Un résumé est affiché dans le terminal à la fin de chaque run.

## Métriques mesurées

| Métrique | Description |
|---|---|
| Latence médiane (ms) | Temps médian par appel sur 5 × 20 items |
| Latence p95 (ms) | 95e percentile des latences |
| Tokens/s | Débit médian (via `eval_count/eval_duration` Ollama) |
| JSON valid % | % d'appels retournant un JSON parseable |
| Schema OK % | % avec `idea` (string) + `details` (liste) présents |
| Visual keywords % | % avec `visual_keywords` présent et non vide |
| Jaccard (qualité) | Similarité Jaccard entre `details` attendus et produits |

## Protocole

1. 1 appel de warm-up non mesuré par modèle
2. 5 répétitions × 20 extraits = 100 appels par modèle
3. Température fixée à 0.1 pour la reproductibilité

## Ajouter un modèle

Éditer `benchmark/config.yaml`, ajouter une entrée dans la liste `models` :

```yaml
  - id: mon-modele:tag
    label: "Mon modèle"
    type: ollama
    lora_path: ""
```

## Hook LoRA (futur)

Le champ `lora_path` dans `config.yaml` est réservé pour le LoRA LLM 2.
Quand un Modelfile avec LoRA sera disponible, renseigner le chemin et adapter
l'adaptateur dans `run_benchmark.py` (section `ollama_chat`).
