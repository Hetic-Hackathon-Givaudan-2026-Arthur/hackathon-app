# Rapport de spike — LLM 1 Analyse de transcription

**Branche :** `20-back-concevoir-architecture-back-a`  
**Date :** 2026-11-12  
**Auteur :** Ahmed

---

## Contexte

Le backend reçoit des transcriptions créatives en français via WebSocket (réunions entre commerciaux et clients Givaudan). Un premier LLM (LLM 1) doit extraire une analyse structurée JSON depuis ces transcriptions, puis la transmettre immédiatement au client. Le résultat visuel (LLM 2 + RAG) est traité en parallèle de manière asynchrone.

Ce spike avait deux objectifs :
1. **Préparer un benchmark** pour choisir le bon modèle LLM 1
2. **Implémenter et tester** le module LLM 1 connecté à Ollama

---

## 1. Benchmark — fichiers créés

### `benchmark/dataset.json`

20 extraits de transcription en français répartis en 4 thèmes :

| Thème | Extraits |
|---|---|
| Identité visuelle | t01 à t05 (minimaliste, luxe, végétal, épicé, romantique) |
| Notes olfactives | t06 à t10 (vanille, marin, musc, bois, rose) |
| Ambiance / émotion | t11 à t15 (nostalgie, urban, zen, oriental, printanier) |
| Références culturelles | t16 à t20 (wabi-sabi, Provence, exploration, scandinave, Afrique) |

Chaque entrée contient :
```json
{
  "id": "t01",
  "theme": "identite_visuelle",
  "transcript": "...",
  "expected": {
    "idea": "...",
    "details": ["...", "..."],
    "visual_keywords": ["...", "..."]
  }
}
```

### `benchmark/config.yaml`

Fichier de configuration des modèles à tester :

```yaml
ollama_base_url: "${OLLAMA_BASE_URL:-http://localhost:11434}"

models:
  - id: qwen2.5:7b
  - id: llama3.1:8b
  - id: qwen2.5:1.5b
  - id: llama3.2:1b
  - id: gemma3:1b

benchmark:
  warmup_calls: 1
  repetitions: 2        # réduit après OOM
  timeout_seconds: 120
```

Champ `lora_path` présent sur chaque modèle (vide) — hook pour brancher un LoRA LLM 2 plus tard.

### `benchmark/run_benchmark.py`

Script Python **sans dépendance externe** (stdlib uniquement) qui :

1. Charge la config YAML avec un parser minimal maison
2. Pour chaque modèle : 1 appel de warm-up puis N répétitions × 20 extraits
3. Mesure par appel :
   - **Latence** (wall-clock en ms)
   - **Tokens/s** via `eval_count / eval_duration` (champs Ollama natifs)
   - **JSON valide** : parseable sans erreur
   - **Schéma OK** : `idea` (string) + `details` (liste) présents
   - **visual_keywords présent** : champ optionnel détecté
   - **Jaccard** : similarité entre `details` attendus et produits
4. Sauvegarde le résultat dans `benchmark/results/<timestamp>.json`
5. Affiche un tableau résumé dans le terminal

**Protocole :** le benchmark a été interrompu par manque de RAM lors du run de `qwen2.5:7b` (modèle de 4.7 GB). Les résultats restent à collecter.

### `benchmark/README.md`

Instructions d'installation, variables d'environnement, commandes de lancement, description des métriques.

---

## 2. ADR — `docs/adr/0005-choix-llm-analyse.md`

ADR au format du projet (statut : **proposée**) décrivant :

- Le contexte : LLM 1 sur chemin critique, transcriptions en français, schéma JSON strict
- Les 5 options avec avantages/inconvénients
- La méthode : benchmark `run_benchmark.py`
- Le tableau de résultats **vide** — à remplir après exécution complète du benchmark
- Les seuils d'acceptation : JSON valid ≥ 95 %, Schema OK ≥ 90 %, Jaccard ≥ 0.30
- Une note sur le LLM 2 / LoRA (spike séparé)

---

## 3. Implémentation LLM 1 — module `backend/llm/llm1_analysis/`

### Schéma JSON attendu

```json
{
  "idea": "Résumé de l'intention principale",
  "details": ["point 1", "point 2", "point 3"],
  "visual_keywords": ["mot1", "mot2", "mot3"]
}
```

> `visual_keywords` est **interne** (non transmis au client via WebSocket). Il sert uniquement au pipeline visuel (LLM 2 + RAG).

---

### `backend/llm/llm1_analysis/schemas.py`

Ajout du champ `visual_keywords` optionnel :

```python
class AnalysisOutput(BaseModel):
    idea: str
    details: list[str]
    visual_keywords: list[str] = Field(default_factory=list)
```

---

### `backend/llm/llm1_analysis/prompts.py`

Prompt renforcé pour les petits modèles (qwen2.5:1.5b) :

- Instruction explicite : **répondre UNIQUEMENT avec un objet JSON valide**
- Pas de bloc markdown, pas de texte avant/après
- Format attendu inlined dans le prompt système
- Température 0.1 fixée côté client pour la reproductibilité

---

### `backend/llm/llm1_analysis/adapter.py`

Parsing JSON **robuste** en deux passes :

1. Nettoyage des blocs ` ```json ``` ` markdown
2. Tentative `json.loads()` directe
3. Si échec : extraction via regex `\{.*\}` (re.DOTALL) puis `json.loads()`
4. Si les deux échouent : `ValueError` avec extrait de la réponse brute

```python
class LLM1Adapter:
    async def call(self, batch_text: str) -> AnalysisOutput:
        messages = build_prompt(batch_text)
        raw = await self._client.complete(messages)
        data = _parse_json(raw)
        return AnalysisOutput(**data)
```

---

### `backend/infrastructure/ollama_client.py`

Nouveau fichier — client HTTP async vers Ollama :

```python
class OllamaClient:
    def __init__(self, base_url=None, model=None):
        self._base_url = base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self._model = model or os.environ.get("LLM1_MODEL", "qwen2.5:1.5b")

    async def complete(self, messages: list[dict]) -> str:
        # POST /api/chat avec httpx.AsyncClient, timeout 120s
        ...
```

**Variables d'environnement :**

| Variable | Défaut | Rôle |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Endpoint Ollama |
| `LLM1_MODEL` | `qwen2.5:1.5b` | Modèle LLM 1 |

---

### `backend/composition/dependencies.py`

Mise à jour : `build_orchestrator` instancie maintenant `OllamaClient` directement depuis les variables d'environnement. Le paramètre `llm_client` a été supprimé de la signature (c'était un placeholder).

```python
def build_orchestrator(ws_manager, outbox_store, redis_url: str) -> Orchestrator:
    llm_client = OllamaClient(
        base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        model=os.environ.get("LLM1_MODEL", "qwen2.5:1.5b"),
    )
    llm1 = LLM1AnalysisService(LLM1Adapter(llm_client))
    ...
```

---

## 4. Smoke test — `backend/test_llm1.py`

Script autonome (pas de dépendance au reste du backend) pour tester l'appel LLM 1 en isolation.

```bash
python backend/test_llm1.py
```

### Résultats obtenus (qwen2.5:1.5b, 2026-11-12)

```
Modèle  : qwen2.5:1.5b
Endpoint: http://localhost:11434

--- test_01 (minimaliste, tons crème) ---
idea            : transmettre la pureté et le naturel sans artifice
details         : ['épuré', 'minimaliste', 'tons crème et ivoire', 'matières naturelles', 'lin', 'coton brut']
visual_keywords : ['épuré', 'minimaliste', 'tons crème et ivoire', 'matières naturelles', 'lin', 'coton brut']
JSON valide     : OK

--- test_02 (vanille Madagascar) ---
idea            : Vanille au cœur
details         : ['vanille charnue', 'note boisée', 'gousse de vanille fraîche de Madagascar']
visual_keywords : ['vanille', 'charnue', 'boisée', 'gousse', 'Madagascar']
JSON valide     : OK
```

**Observations :**
- JSON valide à 100 % sur les deux tests
- Schéma correct (idea + details + visual_keywords)
- Sur un modèle 1.5B, `visual_keywords` tend à répliquer `details` — c'est attendu et acceptable pour la V1
- Latence non mesurée ici (voir benchmark pour les chiffres complets)

---

## 5. Architecture des appels (flux complet)

```
WebSocket reçoit segment
        ↓
orchestrator.handle(IngestSegmentCommand)
        ↓
LLM1AnalysisService.analyze(batch)
        ↓
LLM1Adapter.call(batch_text)
        ↓
OllamaClient.complete(messages)   ←── POST /api/chat  →  Ollama (qwen2.5:1.5b)
        ↓
_parse_json(raw)
        ↓
AnalysisOutput(idea, details, visual_keywords)
        ↓
AnalysisResult(idea, details)     ←── visual_keywords reste interne
        ↓
Pipeline texte  →  WebSocket client
Pipeline visuel →  Redis Streams  →  LLM 2
```

---

## 6. Ce qui reste à faire

| Tâche | Priorité |
|---|---|
| Lancer le benchmark complet (un modèle à la fois pour éviter OOM) | Haute |
| Remplir le tableau de l'ADR 0005 avec les vrais chiffres | Haute |
| Brancher LLM 1 dans le WebSocket endpoint (injection de dépendance) | Haute |
| Implémenter LLM 2 (pipeline visuel) | Moyenne |
| Ajouter `__init__.py` si les imports relatifs posent problème en prod | Basse |
| Spike LoRA LLM 2 quand dataset d'entraînement disponible | Future |
