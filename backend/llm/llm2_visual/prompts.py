SYSTEM_PROMPT = """
Tu es un assistant de recherche visuelle. À partir d'une analyse textuelle,
génère une requête de recherche d'images précise et concise.
Réponds uniquement en JSON valide selon le schéma fourni.
"""

USER_PROMPT_TEMPLATE = """
Analyse :
idea : {idea}
details : {details}
"""


def build_prompt(idea: str, details: list[str]) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_PROMPT_TEMPLATE.format(idea=idea, details=", ".join(details))},
    ]
