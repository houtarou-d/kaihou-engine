# kaihou-engine — Spécification technique détaillée
### Moteur de traduction FR ⇄ EN orchestrant NLP + terminologie + multi-LLM

Version 1.1 — Scope limité à Français ↔ Anglais
Interface v1 : **CLI uniquement**
Organisation en dépôts séparés sous l'umbrella **kaihou-engine** :

- `kaihou-nlp-engine` — brique d'analyse linguistique (existe déjà, à réaligner — voir section 0)
- `kaihou-engine` (ou `kaihou-cli`) — l'orchestrateur/pipeline décrit dans ce document, qui **consomme** `kaihou-nlp-engine` comme dépendance/plugin

---

## 0. Réalignement de `kaihou-nlp-engine` (dépôt existant)

Dépôt de départ : `github.com/houtarou-d/kaihou-nlp-engine` — MIT, structure actuelle :

```
nlp_engine/
├── analyzer.py     # SpaCyAnalyzer, model_map {lang: spacy_model_name}
├── cli.py          # python -m nlp_engine.cli analyze "..." -l en
requirements.txt
install.sh / uninstall.sh
```

**État actuel :** wrapper spaCy qui affiche un arbre POS/dépendances formaté avec Rich, libellés **traduits en espagnol** (`VERB` → *verbo*), pensé comme démo visuelle autonome, pas comme brique consommable par un autre programme.

**Objectif du réalignement :** transformer ce dépôt en **librairie + CLI** qui produit une sortie structurée conforme au contrat `SourceAnalysis` (section 4.1), consommable à la fois en ligne de commande (humain) et par `kaihou-engine` (machine, via subprocess ou import direct).

### 0.1 Changements requis dans `analyzer.py`

1. **Découpler l'analyse de l'affichage.** `SpaCyAnalyzer.analyze()` doit retourner un objet structuré (dataclass ou Pydantic model), jamais imprimer directement. L'affichage Rich devient une couche séparée (`display.py`) qui consomme ce résultat.
2. **Supprimer la traduction des libellés vers l'espagnol** dans la sortie structurée — les tags restent en anglais standard (POS universel : `NOUN`, `VERB`, `ADJ`...). La traduction/localisation d'affichage, si conservée, devient une option `--lang-display` séparée de la langue analysée, uniquement pour le mode humain.
3. **Restreindre `model_map` à FR/EN pour v1** :
   ```python
   model_map = {
       "fr": "fr_core_news_lg",   # ou fr_core_news_trf si dispo
       "en": "en_core_web_trf",
   }
   ```
   (garder l'architecture extensible, mais ne télécharger/documenter que ces deux modèles pour l'instant)
4. **Ajouter l'extraction des entités nommées** (`doc.ents` dans spaCy) — actuellement absent, nécessaire pour la validation en aval (section 8 de ce document).
5. **Ajouter la morphologie détaillée** (`token.morph`) — actuellement le dépôt ne semble extraire que POS + dépendances basiques, il faut aussi `Tense`, `Number`, `Gender`, `Person`, etc. pour alimenter le contexte du LLM.
6. **Format de sortie JSON conforme au schéma `SourceAnalysis`** (voir section 4.1) — ajouter un flag CLI `--json` qui bypasse l'affichage Rich et imprime le JSON structuré sur stdout, pour permettre l'usage en pipe/subprocess par `kaihou-engine`.

### 0.2 Nouvelle interface CLI attendue

```bash
# Mode humain (affichage existant conservé, amélioré)
python -m nlp_engine.cli analyze "Bonjour le monde" -l fr

# Mode machine (nouveau, requis pour intégration kaihou-engine)
python -m nlp_engine.cli analyze "Bonjour le monde" -l fr --json
```

Sortie `--json` attendue : exactement le schéma `SourceAnalysis` (section 4.1), sans `register`/`tone`/`domain` remplis à ce niveau (ces champs sont enrichis plus tard dans le pipeline `kaihou-engine`, pas dans `kaihou-nlp-engine` — ce dépôt reste une brique d'analyse pure, pas de classification).

### 0.3 Ce qui NE doit PAS être ajouté à `kaihou-nlp-engine`

Pour garder la séparation des responsabilités (esprit plugin) :
- ❌ pas de logique LLM ici
- ❌ pas de terminologie/dictionnaire ici
- ❌ pas de classification registre/ton/domaine ici (ça viendra du pipeline `kaihou-engine`, potentiellement en tant que module séparé qui utilise la sortie de `kaihou-nlp-engine` comme input)
- ✅ ce dépôt reste strictement : texte → analyse linguistique structurée

### 0.4 Comment `kaihou-engine` consomme `kaihou-nlp-engine`

Deux options à trancher par l'agent selon simplicité vs performance :

**Option A — subprocess (découplage total, plus simple à démarrer) :**
```python
result = subprocess.run(
    ["python", "-m", "nlp_engine.cli", "analyze", text, "-l", lang, "--json"],
    capture_output=True, text=True
)
analysis = SourceAnalysis.model_validate_json(result.stdout)
```

**Option B — import direct (si `kaihou-nlp-engine` est installé comme package/dépendance) :**
```python
from nlp_engine.analyzer import SpaCyAnalyzer
analyzer = SpaCyAnalyzer()
analysis = analyzer.analyze(text, lang)  # retourne directement le modèle Pydantic
```

**Recommandation :** commencer par l'option A pour la v1 (dépôts indépendants, pas de couplage de dépendances Python), migrer vers B seulement si la latence du subprocess devient un problème mesuré.

### 0.5 Renommage

Le dossier interne `nlp_engine/` peut rester tel quel (pas de raison de casser l'existant), mais le dépôt `kaihou-nlp-engine` doit expliciter dans son README qu'il est un **sous-composant de l'umbrella kaihou-engine**, avec un lien vers le dépôt principal une fois créé.

---

## 1. Objectif

Construire un pipeline de traduction qui, pour une paire de langues (FR↔EN) :

1. Analyse linguistiquement le texte source (syntaxe, morphologie, entités, registre).
2. Enrichit avec terminologie/dictionnaire.
3. Génère un ou plusieurs drafts de traduction via LLM(s).
4. Arbitre entre drafts via un LLM décideur si plusieurs LLM sont utilisés.
5. Valide la traduction (ré-analyse NLP du résultat + comparaison source/cible).
6. Corrige si nécessaire, revalide, produit la sortie finale.

Toute brique doit être remplaçable (architecture plugin). Uniquement des outils FOSS à licence permissive (MIT, Apache 2.0, BSD, MPL) — pas de CC-BY-NC, pas de licences non-OSI sans vérification explicite.

---

## 2. Stack technique recommandée

| Composant | Choix | Licence |
|---|---|---|
| Langage | Python 3.11+ | — |
| NLP engine | spaCy (`en_core_web_trf`, `fr_core_news_lg` ou `_trf`) | MIT |
| NLP engine alternatif | Stanza | Apache 2.0 |
| LLM local runner | Ollama | MIT |
| Modèles LLM candidats | Mistral, Qwen2.5, Llama (vérifier licence usage) | Apache 2.0 / variable |
| Traduction neuronale dédiée (optionnel, baseline) | OPUS-MT (Helsinki-NLP), Argos Translate | Apache 2.0 / MIT |
| Similarité sémantique (validation) | sentence-transformers | Apache 2.0 |
| Alignement mot-à-mot (validation omissions) | eflomal ou fast_align | GPL/BSD (vérifier avant intégration) |
| Validation de schéma de données | Pydantic v2 | MIT |
| Config | YAML (pydantic-settings) | — |
| Async/orchestration | asyncio natif | — |
| Stockage terminologie | SQLite ou fichiers YAML/JSON | — |
| Tests | pytest | — |

---

## 3. Architecture générale

```
kaihou-engine/          # ce dépôt (orchestrateur) — distinct de kaihou-nlp-engine
├── core/
│   ├── pipeline.py              # Pipeline Manager (orchestrateur central)
│   ├── schemas.py               # Modèles Pydantic (contrats de données)
│   ├── config.py                # Chargement configuration YAML
│   └── exceptions.py
├── plugins/
│   ├── base.py                  # Classes abstraites (interfaces plugin)
│   ├── nlp_engines/
│   │   ├── spacy_engine.py
│   │   └── stanza_engine.py
│   ├── terminology/
│   │   ├── glossary_plugin.py
│   │   └── dictionary_plugin.py
│   ├── llm_connectors/
│   │   ├── ollama_connector.py
│   │   └── api_connector.py     # OpenAI-compatible endpoints génériques
│   └── validators/
│       ├── entity_validator.py  # nombres, noms propres, dates
│       ├── terminology_validator.py
│       └── semantic_validator.py # similarité source/cible
├── registry/
│   └── plugin_registry.py       # découverte + instanciation dynamique des plugins
├── config/
│   ├── models.yaml               # profils des LLM (rôle, forces, connector)
│   ├── pipeline.yaml             # ordre des étapes, seuils, mode adaptatif
│   └── glossaries/
│       └── *.yaml
├── cli.py                        # point d'entrée CLI
└── tests/
```

---

## 4. Contrats de données (Pydantic)

### 4.1 `SourceAnalysis` (sortie du NLP engine)

```python
class Token(BaseModel):
    text: str
    lemma: str
    pos: str                # UPOS tag (NOUN, VERB, ADJ...)
    tag: str                # tag détaillé (langue-spécifique)
    morph: dict[str, str]   # ex: {"Tense": "Past", "Number": "Plur"}
    dep: str                # relation de dépendance
    head_index: int
    index: int

class NamedEntity(BaseModel):
    text: str
    label: str               # PERSON, ORG, DATE, GPE, CARDINAL...
    start_char: int
    end_char: int

class SourceAnalysis(BaseModel):
    raw_text: str
    language: str             # "fr" | "en"
    tokens: list[Token]
    entities: list[NamedEntity]
    sentences: list[str]
    register: str | None = None      # formal | informal | technical | neutral
    tone: str | None = None          # neutral | urgent | poetic | assertive...
    domain: str | None = None        # legal | medical | tech | casual...
```

### 4.2 `TerminologyContext`

```python
class TerminologyHit(BaseModel):
    source_term: str
    forced_translation: str | None
    domain: str
    notes: str | None = None

class DictionaryEntry(BaseModel):
    term: str
    definitions: list[str]
    part_of_speech: str
    examples: list[str] = []

class TerminologyContext(BaseModel):
    terminology_hits: list[TerminologyHit]
    dictionary_entries: list[DictionaryEntry]
    cultural_notes: list[str] = []
    regional_variant: str | None = None   # en-US | en-GB | fr-FR | fr-CA
```

### 4.3 `TranslationRequest` (payload complet envoyé au LLM)

```python
class TranslationRequest(BaseModel):
    source_text: str
    source_lang: str
    target_lang: str
    analysis: SourceAnalysis
    terminology: TerminologyContext
    instructions: list[str] = []   # règles imposées, ex: "conserver les majuscules de marque"
```

### 4.4 `LLMDraft`

```python
class LLMDraft(BaseModel):
    llm_id: str
    role: str                 # draft | specialist | decider
    translated_text: str
    self_notes: str | None = None   # remarques du modèle sur ses choix
```

### 4.5 `DecisionResult` (sortie du LLM décideur)

```python
class DecisionResult(BaseModel):
    final_translation: str
    reasoning: str
    chosen_from: dict[str, str]     # ex: {"terminology": "llm_c", "phrasing": "llm_b"}
    confidence: Literal["high", "medium", "low"]
```

### 4.6 `ValidationReport`

```python
class ValidationIssue(BaseModel):
    type: Literal["missing_number", "missing_entity", "added_content",
                   "terminology_violation", "structure_mismatch", "low_semantic_similarity"]
    severity: Literal["critical", "warning", "info"]
    detail: str

class ValidationReport(BaseModel):
    passed: bool
    issues: list[ValidationIssue]
    semantic_similarity_score: float | None = None
```

---

## 5. Interfaces plugin (classes abstraites)

```python
# plugins/base.py
from abc import ABC, abstractmethod

class NLPEnginePlugin(ABC):
    @abstractmethod
    def analyze(self, text: str, lang: str) -> SourceAnalysis: ...

class TerminologyPlugin(ABC):
    @abstractmethod
    def query(self, analysis: SourceAnalysis, domain: str | None) -> TerminologyContext: ...

class LLMConnectorPlugin(ABC):
    profile: LLMProfile   # cf. 6.1

    @abstractmethod
    async def translate(self, request: TranslationRequest) -> LLMDraft: ...

    @abstractmethod
    async def decide(self, request: TranslationRequest,
                      drafts: list[LLMDraft]) -> DecisionResult: ...

class ValidatorPlugin(ABC):
    @abstractmethod
    def validate(self, request: TranslationRequest,
                 result_analysis: SourceAnalysis) -> ValidationReport: ...
```

Chaque plugin concret s'enregistre dans `plugin_registry.py` avec un identifiant unique, permettant au `pipeline.yaml` de référencer les plugins par nom sans coupler le code.

---

## 6. Gestion multi-LLM

### 6.1 Profil LLM (`config/models.yaml`)

```yaml
models:
  - id: mistral_local
    role: draft
    strengths: [general_translation, speed]
    connector: ollama
    connector_config:
      model_name: mistral:7b
      endpoint: http://localhost:11434

  - id: qwen_terminology
    role: specialist
    strengths: [technical_terminology, precision]
    connector: ollama
    connector_config:
      model_name: qwen2.5:14b

  - id: decider_main
    role: decider
    strengths: [reasoning, synthesis]
    connector: api
    connector_config:
      endpoint: https://api.anthropic.com/v1/messages
      model_name: claude-sonnet-4-6
      requires_key: true
```

### 6.2 Mode adaptatif

Défini dans `pipeline.yaml` :

```yaml
adaptive_mode:
  enabled: true
  criteria:
    - if: "domain == 'technical' or sentence_count > 5 or register == 'formal'"
      then: use_full_panel
    - default: single_llm
```

Le Pipeline Manager évalue ces critères juste après l'étape d'analyse NLP (le `domain`/`register` doit être classifié à ce moment — soit par règles heuristiques simples au départ, soit par un petit modèle de classification plus tard).

### 6.3 Flux multi-LLM

1. Pipeline Manager envoie `TranslationRequest` en parallèle (asyncio.gather) à tous les LLM `role: draft` et `role: specialist` activés.
2. Chaque LLM renvoie un `LLMDraft`.
3. Le LLM `role: decider` reçoit `TranslationRequest` + liste de `LLMDraft` → renvoie `DecisionResult`.
4. `DecisionResult.final_translation` devient le candidat à valider.

---

## 7. Pipeline complet (étapes ordonnées)

```python
# core/pipeline.py — logique attendue

def run_pipeline(text: str, source_lang: str, target_lang: str) -> str:
    # 1. Analyse NLP source
    analysis = nlp_engine.analyze(text, source_lang)

    # 2. Classification registre/ton/domaine (heuristique v1, ML plus tard)
    analysis.register, analysis.tone, analysis.domain = classify(analysis)

    # 3. Terminologie + dictionnaire
    term_context = terminology_plugin.query(analysis, analysis.domain)

    # 4. Construction de la requête
    request = TranslationRequest(
        source_text=text, source_lang=source_lang, target_lang=target_lang,
        analysis=analysis, terminology=term_context
    )

    # 5. Décision adaptative : panel complet ou LLM unique
    use_panel = adaptive_decision(analysis)

    # 6. Génération drafts
    if use_panel:
        drafts = await asyncio.gather(*[llm.translate(request) for llm in draft_llms])
        decision = await decider_llm.decide(request, drafts)
        translated = decision.final_translation
    else:
        draft = await default_llm.translate(request)
        translated = draft.translated_text

    # 7. Validation : ré-analyse NLP du résultat
    result_analysis = nlp_engine.analyze(translated, target_lang)

    # 8. Validation croisée
    report = validator.validate(request, result_analysis)

    # 9. Boucle de correction (max N itérations, ex: 2)
    attempts = 0
    while not report.passed and attempts < MAX_CORRECTION_ATTEMPTS:
        correction_request = build_correction_request(request, translated, report)
        draft = await default_llm.translate(correction_request)
        translated = draft.translated_text
        result_analysis = nlp_engine.analyze(translated, target_lang)
        report = validator.validate(request, result_analysis)
        attempts += 1

    return translated
```

---

## 8. Validation — détail des vérifications v1 (FR↔EN)

| Vérification | Méthode | Sévérité |
|---|---|---|
| Nombres présents et identiques | Extraction regex/NER sur source et cible, comparaison ensembliste | critical |
| Noms propres/entités présents | Comparaison `entities` source vs cible (NER spaCy) | critical |
| Terminologie imposée respectée | Recherche des `forced_translation` dans le texte cible | critical |
| Similarité sémantique globale | `sentence-transformers` (modèle multilingue, ex: `paraphrase-multilingual-MiniLM-L12-v2`, Apache 2.0), cosine similarity, seuil ex. 0.80 | warning si < seuil |
| Ratio longueur source/cible anormal | Comparaison nombre de tokens (détecte omissions massives) | warning |
| Structure de phrase cohérente | Nombre de phrases source vs cible comparable | info |

Ne pas tenter de "juger la qualité stylistique" automatiquement en v1 — hors scope, trop risqué en faux positifs.

---

## 9. Terminologie — structure des glossaires (v1)

```yaml
# config/glossaries/tech_fr_en.yaml
domain: technical
entries:
  - source: "conteneur"
    target: "container"
    lang_pair: [fr, en]
    notes: "contexte informatique uniquement, pas 'container' au sens transport"
  - source: "pipeline"
    target: "pipeline"
    lang_pair: [fr, en]
    notes: "ne pas traduire, terme technique établi"
```

Chargement en mémoire au démarrage (SQLite si le volume grossit, sinon YAML suffit pour v1).

---

## 10. CLI minimal attendu (v1)

```bash
kaihou translate --text "Bonjour le monde" --from fr --to en
kaihou translate --file input.txt --from en --to fr --domain technical
kaihou translate --text "..." --from fr --to en --panel   # force le mode multi-LLM
```

Sortie attendue (JSON optionnel avec `--json`) :
```json
{
  "translation": "Hello world",
  "validation": {"passed": true, "issues": []},
  "used_panel": false,
  "llm_used": ["mistral_local"]
}
```

---

## 11. Roadmap de développement (ordre pour l'agent de code)

1. **Squelette + schémas** : `core/schemas.py`, `plugins/base.py`, `plugin_registry.py`
2. **Réalignement de `kaihou-nlp-engine`** (section 0) → mode `--json` conforme à `SourceAnalysis`, restriction FR/EN, ajout entités + morphologie détaillée. Puis wrapper `plugins/nlp_engines/spacy_engine.py` dans `kaihou-engine` qui appelle ce dépôt (option A, subprocess) et valide la sortie contre le schéma Pydantic
3. **LLM connector Ollama** (un seul modèle) → `translate()` fonctionnel
4. **Pipeline linéaire simple** : texte → analyse → LLM unique → sortie (sans validation encore)
5. **Validateur basique** : nombres + entités + longueur
6. **Boucle de correction** (retour au LLM si validation échoue)
7. **Terminologie plugin** (YAML simple) + intégration dans le prompt
8. **CLI** fonctionnel
9. **Tests pytest** sur chaque plugin + pipeline end-to-end
10. **Multi-LLM** : ajout du rôle `specialist` + `decider`, mode adaptatif
11. **Similarité sémantique** (sentence-transformers) dans le validateur
12. **Documentation** (README, exemples d'ajout de plugin)

Chaque étape doit être fonctionnelle et testée avant de passer à la suivante — ne pas paralléliser le développement des étapes 10-11 avant que 1-9 soient stables.

---

## 12. Points de vigilance pour l'agent de code

- Vérifier la licence exacte de chaque modèle LLM téléchargé via Ollama avant intégration (certains "open" ne sont pas OSI-approved).
- Le prompt système envoyé au LLM doit explicitement lister : `analysis`, `terminology`, `register/tone`, et des instructions de format de sortie strict (éviter que le LLM ajoute des commentaires hors traduction — demander un format JSON si besoin de fiabilité).
- Toujours garder un `default_llm` unique fonctionnel comme fallback si le mode panel échoue (timeout, API indisponible).
- Les appels LLM externes (`role: decider` via API) doivent avoir un timeout et un retry avec backoff.
- Ne jamais bloquer le pipeline entier si un plugin optionnel (ex: cultural_notes) échoue — logger et continuer avec une valeur vide.
