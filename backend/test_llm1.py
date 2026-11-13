"""
Smoke test LLM 1 — appel direct à Ollama via OllamaClient + LLM1Adapter.
Usage depuis la racine du projet :
    python backend/test_llm1.py
"""

import asyncio
import json
import sys
import os

# Permet d'importer les modules backend sans installation
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from infrastructure.ollama_client import OllamaClient
from llm.llm1_analysis.adapter import LLM1Adapter

TRANSCRIPTS = [
    {
        "id": "test_01",
        "text": (
            "On cherche quelque chose de très épuré, presque minimaliste. "
            "Des tons crème et ivoire, des matières naturelles, du lin, du coton brut. "
            "L'idée c'est de transmettre la pureté, le naturel, sans artifice."
        ),
    },
    {
        "id": "test_02",
        "text": (
            "La vanille est au cœur de la composition. Une vanille charnue, presque sucrée, "
            "avec une note boisée en fond. On pense à une gousse de vanille fraîche de Madagascar, "
            "chaleureuse, enveloppante."
        ),
    },
    {
    "id": "test_03",
    "text": "On veut une image de marque autour du jasmin, quelque chose de floral mais pas sucré, plutôt élégant.",
},
]


async def main():
    client = OllamaClient()
    adapter = LLM1Adapter(client)

    print(f"Modèle : {client._model}")
    print(f"Endpoint : {client._base_url}\n")

    for item in TRANSCRIPTS:
        print(f"--- {item['id']} ---")
        print(f"Transcription : {item['text'][:80]}...")
        try:
            result = await adapter.call(item["text"])
            print(f"idea            : {result.idea}")
            print(f"details         : {result.details}")
            print(f"visual_keywords : {result.visual_keywords}")
            print(f"JSON valide     : OK")
        except ValueError as e:
            print(f"ERREUR parsing  : {e}")
        except Exception as e:
            print(f"ERREUR appel    : {e}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
