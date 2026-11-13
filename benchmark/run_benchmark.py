"""
Benchmark LLM 1 — Analyse de transcription (idea + details + visual_keywords)
Prérequis : Python 3.9+, Ollama actif, pas de dépendance externe.
Usage    : python benchmark/run_benchmark.py [--config benchmark/config.yaml]
"""

import json
import os
import re
import statistics
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEFAULT_CONFIG = Path(__file__).parent / "config.yaml"

SYSTEM_PROMPT = """Tu es un assistant expert en identité de marque et en parfumerie.
Tu reçois une transcription d'une réunion créative en français.
Tu dois extraire les informations clés et répondre UNIQUEMENT avec un objet JSON valide,
sans texte avant ni après, sans bloc markdown.

Format attendu :
{
  "idea": "une phrase résumant l'intention principale",
  "details": ["point 1", "point 2", "point 3"],
  "visual_keywords": ["mot1", "mot2", "mot3"]
}

Règles :
- "idea" : string, 1 phrase courte en français
- "details" : liste de 3 à 6 strings en français
- "visual_keywords" : liste de 5 à 10 mots-clés en français pour recherche visuelle
- Ne pas inventer d'informations absentes de la transcription
"""

USER_TEMPLATE = "Transcription : {transcript}"


# ---------------------------------------------------------------------------
# YAML minimal parser (stdlib only — pas de PyYAML)
# ---------------------------------------------------------------------------

def load_config(path: Path) -> dict:
    """Parse le config.yaml de façon minimale (clés simples et listes de dicts)."""
    base_url_env = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

    models = []
    benchmark = {"warmup_calls": 1, "repetitions": 5, "timeout_seconds": 120, "results_dir": "results"}

    current_model: dict | None = None
    in_models = False
    in_benchmark = False

    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip()
            stripped = line.lstrip()
            if not stripped or stripped.startswith("#"):
                continue

            if line.startswith("ollama_base_url"):
                val = line.split(":", 1)[1].strip().strip('"')
                if val.startswith("${") and ":-" in val:
                    base_url_env = val.split(":-")[1].rstrip("}")
                continue

            if line.startswith("models:"):
                in_models = True
                in_benchmark = False
                continue

            if line.startswith("benchmark:"):
                if current_model:
                    models.append(current_model)
                    current_model = None
                in_models = False
                in_benchmark = True
                continue

            if in_models:
                indent = len(line) - len(stripped)
                if indent == 2 and stripped.startswith("- "):
                    if current_model:
                        models.append(current_model)
                    key, val = stripped[2:].split(":", 1)
                    current_model = {key.strip(): val.strip().strip('"')}
                elif indent == 4 and current_model is not None:
                    key, val = stripped.split(":", 1)
                    current_model[key.strip()] = val.strip().strip('"')

            if in_benchmark and ":" in stripped:
                key, val = stripped.split(":", 1)
                k, v = key.strip(), val.strip()
                if v.isdigit():
                    benchmark[k] = int(v)
                else:
                    benchmark[k] = v

    if current_model:
        models.append(current_model)

    return {
        "ollama_base_url": os.environ.get("OLLAMA_BASE_URL", base_url_env),
        "models": models,
        "benchmark": benchmark,
    }


# ---------------------------------------------------------------------------
# Ollama client
# ---------------------------------------------------------------------------

def ollama_chat(base_url: str, model_id: str, transcript: str, timeout: int) -> dict:
    """Appelle /api/chat d'Ollama. Retourne le dict de la réponse."""
    payload = {
        "model": model_id,
        "stream": False,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_TEMPLATE.format(transcript=transcript)},
        ],
        "options": {"temperature": 0.1},
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{base_url}/api/chat",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


# ---------------------------------------------------------------------------
# Validation JSON et schéma
# ---------------------------------------------------------------------------

def parse_llm_output(raw: str) -> tuple[bool, dict | None]:
    """Tente de parser le JSON dans la réponse brute."""
    # Nettoyage des blocs markdown ```json ... ```
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    # Extraction du premier objet JSON trouvé
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        return False, None
    try:
        obj = json.loads(match.group())
        return True, obj
    except json.JSONDecodeError:
        return False, None


def validate_schema(obj: dict) -> dict:
    """Vérifie la conformité au schéma. Retourne un dict de flags."""
    has_idea = isinstance(obj.get("idea"), str) and len(obj["idea"]) > 0
    has_details = (
        isinstance(obj.get("details"), list)
        and len(obj["details"]) >= 1
        and all(isinstance(x, str) for x in obj["details"])
    )
    has_vk = (
        isinstance(obj.get("visual_keywords"), list)
        and len(obj["visual_keywords"]) >= 1
        and all(isinstance(x, str) for x in obj["visual_keywords"])
    )
    return {
        "schema_ok": has_idea and has_details,
        "has_idea": has_idea,
        "has_details": has_details,
        "has_visual_keywords": has_vk,
    }


# ---------------------------------------------------------------------------
# Qualité : Jaccard sur les mots-clés
# ---------------------------------------------------------------------------

def tokenize(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.lower()))


def jaccard(expected_items: list[str], actual_items: list[str]) -> float:
    """Jaccard sur l'union des tokens entre expected et actual."""
    if not expected_items or not actual_items:
        return 0.0
    exp = set()
    for s in expected_items:
        exp |= tokenize(s)
    act = set()
    for s in actual_items:
        act |= tokenize(s)
    if not exp and not act:
        return 1.0
    return len(exp & act) / len(exp | act)


# ---------------------------------------------------------------------------
# Benchmark d'un seul modèle
# ---------------------------------------------------------------------------

def benchmark_model(cfg: dict, model_cfg: dict, dataset: list) -> dict:
    base_url = cfg["ollama_base_url"]
    model_id = model_cfg["id"]
    timeout = cfg["benchmark"]["timeout_seconds"]
    reps = cfg["benchmark"]["repetitions"]
    warmup = cfg["benchmark"]["warmup_calls"]

    print(f"\n{'='*60}")
    print(f"Modèle : {model_id}")
    print(f"{'='*60}")

    # Warm-up
    print(f"  Warm-up ({warmup} appel(s))...", end=" ", flush=True)
    for _ in range(warmup):
        try:
            ollama_chat(base_url, model_id, dataset[0]["transcript"], timeout)
        except Exception as e:
            print(f"\n  ERREUR warm-up : {e}")
            return {"model_id": model_id, "error": str(e), "runs": []}
    print("OK")

    all_latencies: list[float] = []
    all_tokens_per_s: list[float] = []
    json_valid_count = 0
    schema_ok_count = 0
    vk_ok_count = 0
    quality_scores: list[float] = []
    total_calls = 0

    for rep in range(1, reps + 1):
        print(f"  Répétition {rep}/{reps} : ", end="", flush=True)
        for item in dataset:
            total_calls += 1
            t0 = time.monotonic()
            try:
                resp = ollama_chat(base_url, model_id, item["transcript"], timeout)
            except urllib.error.URLError as e:
                print(f"\n  ERREUR appel {item['id']}: {e}")
                all_latencies.append(timeout * 1000)
                continue
            except Exception as e:
                print(f"\n  ERREUR appel {item['id']}: {e}")
                all_latencies.append(timeout * 1000)
                continue
            latency_ms = (time.monotonic() - t0) * 1000
            all_latencies.append(latency_ms)

            # Tokens/s via champs Ollama (eval_count / eval_duration en nanosecondes)
            eval_count = resp.get("eval_count", 0)
            eval_duration_ns = resp.get("eval_duration", 0)
            if eval_count and eval_duration_ns:
                tps = eval_count / (eval_duration_ns / 1e9)
                all_tokens_per_s.append(tps)

            raw_text = resp.get("message", {}).get("content", "")
            json_ok, parsed = parse_llm_output(raw_text)
            if json_ok:
                json_valid_count += 1
            if json_ok and parsed:
                flags = validate_schema(parsed)
                if flags["schema_ok"]:
                    schema_ok_count += 1
                if flags["has_visual_keywords"]:
                    vk_ok_count += 1
                # Qualité : Jaccard sur details
                score = jaccard(item["expected"]["details"], parsed.get("details", []))
                quality_scores.append(score)
            print(".", end="", flush=True)
        print()

    print(f"  Total appels : {total_calls}")

    result = {
        "model_id": model_id,
        "label": model_cfg.get("label", model_id),
        "total_calls": total_calls,
        "latency_median_ms": round(statistics.median(all_latencies), 1) if all_latencies else None,
        "latency_p95_ms": round(sorted(all_latencies)[int(len(all_latencies) * 0.95)], 1) if all_latencies else None,
        "tokens_per_s_median": round(statistics.median(all_tokens_per_s), 1) if all_tokens_per_s else None,
        "json_valid_pct": round(json_valid_count / total_calls * 100, 1),
        "schema_ok_pct": round(schema_ok_count / total_calls * 100, 1),
        "visual_keywords_present_pct": round(vk_ok_count / total_calls * 100, 1),
        "quality_jaccard_mean": round(statistics.mean(quality_scores), 3) if quality_scores else None,
        "quality_jaccard_median": round(statistics.median(quality_scores), 3) if quality_scores else None,
    }

    print(f"  Latence médiane  : {result['latency_median_ms']} ms")
    print(f"  Latence p95      : {result['latency_p95_ms']} ms")
    print(f"  Tokens/s         : {result['tokens_per_s_median']}")
    print(f"  JSON valide      : {result['json_valid_pct']} %")
    print(f"  Schéma OK        : {result['schema_ok_pct']} %")
    print(f"  Visual keywords  : {result['visual_keywords_present_pct']} %")
    print(f"  Jaccard (qualité): {result['quality_jaccard_mean']}")

    return result


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

def main():
    config_path = Path(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[1] == "--config" else DEFAULT_CONFIG
    if not config_path.exists():
        print(f"Config introuvable : {config_path}", file=sys.stderr)
        sys.exit(1)

    cfg = load_config(config_path)
    dataset_path = Path(__file__).parent / "dataset.json"
    with open(dataset_path, encoding="utf-8") as f:
        dataset = json.load(f)

    print(f"Dataset : {len(dataset)} extraits")
    print(f"Modèles : {[m['id'] for m in cfg['models']]}")
    print(f"Répétitions : {cfg['benchmark']['repetitions']}")
    print(f"Endpoint : {cfg['ollama_base_url']}")

    results = []
    for model_cfg in cfg["models"]:
        r = benchmark_model(cfg, model_cfg, dataset)
        results.append(r)

    # Sauvegarde
    results_dir = Path(__file__).parent / cfg["benchmark"]["results_dir"]
    results_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = results_dir / f"benchmark_{stamp}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"timestamp": stamp, "config": cfg, "results": results}, f, ensure_ascii=False, indent=2)

    print(f"\nRésultats sauvegardés : {out_path}")

    # Résumé console
    print("\n" + "=" * 80)
    print(f"{'Modèle':<22} {'Med ms':>7} {'p95 ms':>7} {'Tok/s':>7} {'JSON%':>6} {'Schema%':>8} {'Jaccard':>8}")
    print("-" * 80)
    for r in results:
        if "error" in r:
            print(f"{r['model_id']:<22}  ERREUR : {r['error']}")
            continue
        print(
            f"{r['model_id']:<22}"
            f" {str(r['latency_median_ms']):>7}"
            f" {str(r['latency_p95_ms']):>7}"
            f" {str(r['tokens_per_s_median']):>7}"
            f" {str(r['json_valid_pct']):>6}"
            f" {str(r['schema_ok_pct']):>8}"
            f" {str(r['quality_jaccard_mean']):>8}"
        )
    print("=" * 80)


if __name__ == "__main__":
    main()
