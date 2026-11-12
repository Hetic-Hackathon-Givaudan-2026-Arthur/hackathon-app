SYSTEM_PROMPT = """
Tu es un assistant d'analyse de conversation. Extrait les informations structurées suivantes :
- idea : l'idée principale exprimée
- details : liste de faits ou éléments visuels mentionnés
Réponds uniquement en JSON valide selon le schéma fourni.
"""

USER_PROMPT_TEMPLATE = """
Transcription :
{text}
"""


def build_prompt(text: str) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_PROMPT_TEMPLATE.format(text=text)},
    ]
