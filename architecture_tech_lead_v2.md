# Architecture technique --- Analyse conversationnelle et enrichissement visuel

**Document de cadrage technique · Version 1.0**

## 1. Objectif

Mettre en place un service capable de recevoir en continu une
transcription produite par un outil local, d'en extraire des
informations avec un LLM, puis d'enrichir chaque résultat avec des
images pertinentes.

Le système doit garantir que le résultat textuel est transmis
immédiatement, sans attendre la recherche visuelle. Les deux traitements
sont indépendants et corrélés par un identifiant d'analyse.

## 2. Architecture fonctionnelle

``` mermaid
flowchart TD
    A["Outil local de transcription"] -->|WebSocket| B["API / Gateway"]
    B --> C["Buffer de transcription"]
    C --> D["Ordonnanceur de lots"]
    D --> E["LLM 8B — Analyse et extraction"]
    E --> F["Orchestrateur"]
    F --> G["Pipeline texte"]
    F --> Q["Queue visuelle durable — Redis Streams"]
    Q --> H["Worker LLM 2 — Consommateur FIFO"]
    G --> I["Outbox / WebSocket"]
    H --> J["Snapshot de mémoire analytique"]
    J --> K["LLM 2 spécialisé / LoRA"]
    K --> L["Références visuelles"]
    L --> M["Sélection des images"]
    M --> I
    I --> N["Client"]
    B -.-> O["Journal d'événements"]
    E -.-> O
    F -.-> O
    G -.-> O
    H -.-> O
    L -.-> O
    I -.-> O
```

## 3. Composants et responsabilités

  -----------------------------------------------------------------------
  Composant                           Responsabilité
  ----------------------------------- -----------------------------------
  Gateway WebSocket                   Réception des segments et émission
                                      des résultats

  Buffer de transcription             Accumulation et constitution de
                                      lots

  Ordonnanceur                        Déclenchement des lots selon seuils
                                      et délais

  LLM 8B                              Analyse des segments et extraction
                                      structurée

  Orchestrateur                       Création de l'analyse et
                                      déclenchement des pipelines

  Pipeline texte                      Transmission immédiate du résultat
                                      au client

  Mémoire analytique                  Consolidation des informations
                                      extraites

  Pipeline visuel                     Recherche asynchrone d'images
                                      associées

  Références visuelles                Récupération des références
                                      visuelles pertinentes

  Processing Log                      Traçabilité des entrées,
                                      traitements et livraisons

  Outbox                              Fiabilisation des événements à
                                      transmettre
  -----------------------------------------------------------------------

## 4. Flux de traitement

1. Le client transmet les segments de transcription au serveur via WebSocket.
2. Le serveur les place dans un buffer indépendant de l'inférence.
3. L'ordonnanceur constitue un lot et le transmet au **LLM 1**, chargé de l'analyse textuelle.
4. Le LLM 1 retourne une analyse structurée et l'orchestrateur lui attribue un `analysis_id`.
5. L'orchestrateur déclenche deux branches indépendantes :
   - **Pipeline A — Texte :** enregistrement/outbox puis envoi immédiat de `analysis_result` au client.
   - **Pipeline B — Visuel :** publication durable du résultat et de son `analysis_id`.
6. Un worker indépendant récupère la prochaine tâche de la file et la transmet au **LLM 2**, qui construit la requête visuelle avant le RAG et la recherche d'images.
7. Pendant que le LLM 2 traite une tâche, le LLM 1 continue à analyser les nouveaux lots. Les nouveaux résultats s'accumulent dans la file si le LLM 2 est plus lent.
8. Le worker acquitte la tâche après traitement durable. En cas d'échec, la tâche peut être reprise sans relancer l'analyse textuelle.
9. Le pipeline visuel transmet les images trouvées avec le même `analysis_id`. Le client les rattache au résultat textuel, quel que soit l'ordre d'arrivée.

**Invariant : le LLM 1 ne doit jamais attendre le LLM 2, le RAG ou le retour des images.** La file découple les cadences des deux modèles. Pour la V1, un worker visuel consomme en FIFO ; plusieurs workers peuvent être ajoutés ensuite si nécessaire, en acceptant que les recherches se terminent dans un ordre différent de celui de la file.

## 5. Contrat WebSocket

### Résultat textuel

``` json
{
  "event": "analysis_result",
  "session_id": "session_001",
  "analysis": {
    "analysis_id": "analysis_0042",
    "text": {
      "idea": "Identité visuelle naturelle et épurée",
      "details": [
        "Utilisation de tons crème",
        "Mise en avant de la vanille"
      ]
    }
  }
}
```

### Résultat visuel

Le résultat visuel utilise le même `session_id` et le même
`analysis_id`.

Le contenu de l'image est transmis en binaire, et non sous forme d'URL
ou de Base64 dans le JSON. Une trame de contrôle annonce les images et
leurs identifiants ; les trames binaires suivantes transportent les
octets, selon un ordre et un protocole de framing documentés.

Trame de contrôle :

``` json
{
  "event": "visual_result",
  "session_id": "session_001",
  "analysis": {
    "analysis_id": "analysis_0042",
    "images": [
      {
        "image_id": "img_0081",
        "content_type": "image/webp",
        "byte_length": 48231
      }
    ]
  }
}
```

Le client associe les octets reçus à `image_id`, puis l'image à
`analysis_id`.

## 6. Traçabilité et fiabilité

Le Processing Log conserve les événements de traitement de manière
append-only. Il permet de reconstituer le parcours d'une analyse sans
exposer les informations internes au client.

Événements principaux :

-   `transcript.received`
-   `batch.created`
-   `analysis.started`
-   `analysis.completed`
-   `text.delivery.queued`
-   `text.delivery.sent`
-   `visual.task.queued`
-   `visual.search.started`
-   `visual.search.completed`
-   `visual.delivery.queued`
-   `visual.delivery.sent`
-   `processing.failed`
-   `processing.retried`

L'outbox est distincte du journal : elle conserve les événements qui
doivent être transmis et permet leur reprise après déconnexion ou erreur
d'envoi.

Garanties attendues :

-   Identifiants stables et idempotence des segments, lots et tâches.
-   Corrélation par `session_id` et `analysis_id`.
-   Réception WebSocket non bloquante.
-   Le LLM 1 continue sans attendre le LLM 2 ; les résultats visuels en attente sont conservés dans Redis Streams.
-   Consommation FIFO par un worker en V1 ; workers supplémentaires possibles ensuite, avec résultats potentiellement désordonnés.
-   Reprise des tâches non acquittées et idempotence pour éviter les doublons.
-   Surveillance de la profondeur et de l'ancienneté de la file, avec limites et politique de retry.
-   Accusé de réception applicatif si la confirmation d'affichage côté
    client est requise.
-   Gestion des reprises et des échecs sans dupliquer les résultats.

## 7. Stack technique cible

  Couche                          Technologie proposée
  ------------------------------- ----------------------------------------------
  Backend / API                   Python
  WebSocket                       FastAPI
  Buffer et files de tâches       Redis Streams
  LLM                             Qwen 8B ou modèle équivalent
  
Les technologies sont des choix cibles, à confirmer lors du
dimensionnement et des tests de compatibilité. Les contrats d'événements
et les identifiants de corrélation doivent rester indépendants des
implémentations.

## 8. Décisions structurantes

-   Le LLM 1 produit le texte en continu et le résultat textuel est prioritaire.
-   Chaque résultat validé est publié dans une file visuelle durable ; le LLM 2 la consomme à son rythme sans bloquer le LLM 1.
-   La recherche d'images est asynchrone et indépendante.
-   `analysis_id` est la clé de rattachement entre texte, tâche visuelle
    et images.
-   Le payload client ne contient ni score de pertinence ni détails
    internes du RAG.
-   Le journal interne est append-only ; l'outbox assure la livraison.
-   Les images sont transmises en trames binaires WebSocket, avec trames
    de contrôle JSON.

## 9. Architecture applicative proposée

### 9.1 Entrée, orchestrateur et séparation des traitements

L'entrée applicative constitue un point d'adaptation unique. Elle valide
le contrat entrant, attribue ou vérifie le `session_id` et le
`segment_id`, puis transmet une commande interne à l'orchestrateur. Elle
ne contient aucune logique spécifique aux modèles LLM.

``` mermaid
flowchart LR
    A["Entrée WebSocket / API"] --> B["Commande interne"]
    B --> C["Orchestrateur"]
    C --> D["Buffer + ordonnanceur"]
    D --> E["LLM 1 — Analyse"]
    E --> F["Résultat d'analyse"]
    F --> G["Pipeline texte"]
    F --> H["File visuelle"]
    H --> I["LLM 2 — Recherche visuelle"]
    I --> J["RAG + images"]
    G --> K["Outbox / Client"]
    J --> K
```

L'orchestrateur coordonne uniquement le flux et les contrats. Il ne
connaît ni le framework WebSocket, ni l'implémentation du fournisseur
LLM, ni le moteur de recherche d'images. Chaque dépendance est injectée
derrière une interface ciblée.

### 9.2 Organisation des dossiers par LLM

La séparation par modèle rend explicites les responsabilités et permet
de remplacer ou de faire évoluer un modèle sans déplacer la logique
métier commune.

``` text
src/
  entrypoints/
    websocket_api.py
    http_api.py
  application/
    orchestrator.py
    commands.py
    ports/
      analysis_model.py
      visual_model.py
      event_publisher.py
      task_queue.py
      result_delivery.py
  domain/
    analysis/
      entities.py
      value_objects.py
      policies.py
    events.py
  llm/
    llm1_analysis/
      prompts.py
      schemas.py
      adapter.py
      service.py
    llm2_visual/
      prompts.py
      schemas.py
      adapter.py
      service.py
  pipelines/
    text/
      service.py
    visual/
      service.py
      rag.py
      image_search.py
  infrastructure/
    redis_streams.py
    outbox.py
    processing_log.py
  composition/
    dependencies.py
```

Rôle de chaque fichier :

| Fichier | Rôle |
|---|---|
| `entrypoints/websocket_api.py` | Reçoit les segments par WebSocket, valide le format entrant et transmet une commande interne. |
| `entrypoints/http_api.py` | Expose les éventuels endpoints HTTP nécessaires au service, sans logique métier. |
| `application/orchestrator.py` | Coordonne le flux complet : analyse, livraison text e et création de la tâche visuelle. |
| `application/commands.py` | Définit les commandes internes utilisées entre l'entrée et les cas d'usage. |
| `application/ports/analysis_model.py` | Contrat minimal du LLM 1 chargé de l'analyse textuelle. |
| `application/ports/visual_model.py` | Contrat minimal du LLM 2 chargé de préparer la recherche visuelle. |
| `application/ports/event_publisher.py` | Contrat de publication des événements de traitement. |
| `application/ports/task_queue.py` | Contrat d'ajout, de lecture et d'acquittement des tâches visuelles. |
| `application/ports/result_delivery.py` | Contrat de livraison des résultats au client. |
| `domain/analysis/entities.py` | Entités métier d'une analyse, d'un segment et d'un lot. |
| `domain/analysis/value_objects.py` | Identifiants et valeurs contrôlées comme `session_id`, `segment_id` et `analysis_id`. |
| `domain/analysis/policies.py` | Règles d'idempotence, de validation et de transition d'état. |
| `domain/events.py` | Événements métier indépendants des outils techniques. |
| `llm/llm1_analysis/prompts.py` | Prompts du LLM 1 pour extraire l'information structurée. |
| `llm/llm1_analysis/schemas.py` | Schémas d'entrée et de sortie attendus par le LLM 1. |
| `llm/llm1_analysis/adapter.py` | Adaptateur concret vers le fournisseur ou le moteur du LLM 1. |
| `llm/llm1_analysis/service.py` | Cas d'usage d'analyse du texte avec le LLM 1. |
| `llm/llm2_visual/prompts.py` | Prompts du LLM 2 pour construire les requêtes visuelles. |
| `llm/llm2_visual/schemas.py` | Schémas d'entrée et de sortie attendus par le LLM 2. |
| `llm/llm2_visual/adapter.py` | Adaptateur concret vers le fournisseur ou le moteur du LLM 2. |
| `llm/llm2_visual/service.py` | Cas d'usage de préparation de la recherche visuelle. |
| `pipelines/text/service.py` | Publie rapidement le résultat textuel via la sortie prévue. |
| `pipelines/visual/service.py` | Exécute la branche visuelle sans bloquer la branche texte. |
| `pipelines/visual/rag.py` | Recherche les références visuelles à partir du contexte produit par le LLM 2, sans imposer de moteur de stockage. |
| `pipelines/visual/image_search.py` | Interroge le fournisseur d'images et normalise les résultats retournés. |
| `infrastructure/redis_streams.py` | Implémente la file durable des tâches visuelles avec Redis Streams. |
| `infrastructure/outbox.py` | Conserve les résultats à transmettre et permet leur reprise après une déconnexion. |
| `infrastructure/processing_log.py` | Écrit le journal append-only des étapes, erreurs et reprises du traitement. |
| `composition/dependencies.py` | Assemble les implémentations concrètes et injecte les dépendances au démarrage. |

Les dossiers `llm1_analysis` et `llm2_visual` contiennent les adaptateurs,
prompts et schémas propres à chaque modèle. Les règles de corrélation,
d'idempotence et de cycle de vie de l'analyse restent dans `domain` et
`application`, afin de ne pas dépendre d'un modèle particulier.

### 9.3 Étapes de l'analyse

Le traitement d'un lot suit les étapes suivantes :

1. **Réception :** validation du segment et déduplication par
   `session_id` + `segment_id`.
2. **Constitution du lot :** regroupement selon le seuil ou le délai
   configuré.
3. **Analyse LLM 1 :** extraction structurée de l'intention, des faits
   et des éléments visuels potentiels.
4. **Validation métier :** contrôle du schéma, génération de
   l'`analysis_id` et enregistrement de l'événement `analysis.completed`.
5. **Branche texte :** publication immédiate via l'outbox.
6. **Branche visuelle :** publication d'une tâche durable dans Redis
   Streams.
7. **Analyse LLM 2 :** construction de la requête visuelle, récupération
   RAG, sélection et préparation des images.
8. **Livraison visuelle :** envoi des images avec le même
   `session_id` et le même `analysis_id`.

Chaque étape est idempotente et peut être rejouée à partir de son
événement durable. Une erreur de la branche visuelle ne relance pas
l'analyse textuelle déjà livrée.

### 9.4 Clean Architecture pragmatique : SOLID et YAGNI

La conception suit une Clean Architecture minimale, adaptée au périmètre
V1 :

- **Domaine :** entités, identifiants, invariants et événements métier ;
  aucune dépendance technique.
- **Application :** cas d'usage et orchestration ; dépend uniquement des
  ports nécessaires.
- **Infrastructure :** Redis Streams, WebSocket, fichiers et fournisseurs
  LLM ; implémente les ports de l'application.
- **Entrypoints :** conversion des requêtes externes en commandes et des
  résultats internes en réponses.

Les principes SOLID s'appliquent de façon ciblée :

- **Responsabilité unique :** un service orchestre, un adaptateur appelle
  un modèle, un composant écrit un événement ou livre un résultat.
- **Ouvert/fermé :** un nouveau fournisseur LLM ou une nouvelle file
  s'ajoute par implémentation d'un port.
- **Substitution :** les implémentations de test remplacent les
  fournisseurs réels sans modifier les cas d'usage.
- **Ségrégation :** les ports sont petits (`AnalysisModel`,
  `VisualModel`, `TaskQueue`, `ResultDelivery`).
- **Inversion des dépendances :** l'application dépend d'abstractions ;
  la composition assemble les implémentations concrètes.

YAGNI limite volontairement la V1 : pas de bus de messages générique,
pas de framework de plugins, pas de microservices séparés, pas de
hiérarchie de classes pour les modèles et pas de pipeline configurable
par DSL. Ces abstractions ne seront introduites que lorsqu'un besoin
réel, mesuré et récurrent le justifiera.
