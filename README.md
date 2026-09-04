# Kaihou Engine – Advanced French ↔ English Translation Orchestrator

**kaihou‑engine** is a fully‑featured translation orchestrator that wraps an LLM (local via Ollama or remote API) with linguistic analysis, terminology enforcement, and automatic validation/correction. It produces translations that are far more **controlled** and **verifiable** than a raw LLM call.

> **Status:** 🚧 Active development – version 1.x (FR ↔ EN) with a CLI interface is in progress.

---

## Why This Project Exists

| Raw LLM call | What kaihou‑engine adds |
|--------------|------------------------|
| Fast but unpredictable: technical terms can be missed, numbers / proper names get mangled, tone is not preserved. | <ul><li>**Linguistic analysis** (syntax, morphology, entities) via `kaihou‑nlp‑engine` (spaCy).</li><li>**Terminology enforcement** using domain glossaries.</li><li>**Validation** of numbers, entities, terminology, and semantic similarity.</li><li>**Automatic correction loop** – the LLM revises drafts that fail validation.</li><li>**Multi‑LLM panel** – run several LLMs in parallel and let a “decider” choose the best draft.</li></ul> |
| No guarantee of quality. | **Deterministic, auditable pipeline** – every step is a pluggable component, fully testable, and the full trace can be output as JSON. |

All code is **100 % FOSS** under permissive licenses (MIT, Apache 2.0, BSD, MPL).

---

## Architecture Overview

```
Source text
   │
   ▼
kaihou‑nlp‑engine ──▶ Linguistic analysis (syntax, morphology, entities)
   │
   ▼
Terminology / Glossary lookup
   │
   ▼
LLM(s) ──▶ Draft translation(s)
   │
   ▼
LLM Decider (optional, when several LLMs are used) ──▶ Chosen draft
   │
   ▼
kaihou‑nlp‑engine ──▶ Re‑analysis of the draft
   │
   ▼
Validation (numbers, entities, terminology, semantic similarity)
   ├── Failure ──▶ LLM‑based correction ──▶ Re‑validation (loop)
   └── Success ──▶ Final translation output
```

Every block is a **plugin** that implements an abstract interface defined in `kaihou_engine/plugins/base.py`. Swapping the NLP engine, LLM model, or glossary never requires touching the core pipeline.

---

## Repository Layout

```
kaihou-engine/
├─ .github/                # CI & publishing workflows
├─ config/
│   ├─ models.yaml          # LLM profiles (connector, strengths, etc.)
│   ├─ pipeline.yaml        # Order of steps, thresholds, adaptive‑mode rules
│   ├─ glossaries/          # Domain‑specific term glossaries (YAML)
│   └─ plugins.yaml         # List of enabled plugins (by module path)
├─ src/kaihou_engine/
│   ├─ __init__.py
│   ├─ orchestrator.py      # CLI entry point (`kaihou` console script)
│   ├─ core/                # Pipeline runner, schemas, exceptions
│   └─ plugins/             # LLM connectors, terminologists, validators, etc.
├─ .gitignore
├─ pyproject.toml
└─ README.md                # (this file)
```

The **pure linguistic analysis library** lives in a separate repository:

| Repository | Role |
|------------|------|
| `kaihou-nlp-engine` | spaCy‑based tokenisation, POS, morphology, dependency parsing, named‑entity extraction. |
| **`kaihou-engine`** (this repo) | Orchestrator: pipeline, terminology, LLM connectors, validation, CLI |

All components are designed as **replaceable plugins** (abstract interfaces in `plugins/base.py`). Changing the NLP engine, LLM model, or glossary does not require any code modification elsewhere.

---

## Core Features

- **Structured linguistic analysis** via `kaihou‑nlp‑engine`.  
- **Translation** using a local LLM (Ollama) **or** a remote API.  
- **Domain glossaries** for deterministic terminology handling.  
- **Automatic validation** of numbers, entities, terminology, and semantic similarity.  
- **Self‑correcting loop** – failing drafts are sent back to the LLM for revision.  
- **Multi‑LLM panel** with a decider plugin (chooses the best draft).  
- **Adaptive mode** – automatically switches between single‑LLM and panel based on text complexity.  
- **Full JSON output** (`--json`) that contains the translation, the whole debug trace, and validation details.

---

## Installation

### 1️⃣  Clone the repository
```bash
git clone https://github.com/houtarou-d/kaihou-engine.git
cd kaihou-engine
```

### 2️⃣  Set up the development environment
```bash
# The provided setup script creates a virtual environment,
# activates it, upgrades pip/setuptools/wheel and installs the
# package in editable mode.
./setup.sh               # normal install
# or, with development extras (tests, linting, etc.)
./setup.sh --dev
```

### 3️⃣  Install the required linguistic engine
```bash
git clone https://github.com/houtarou-d/kaihou-nlp-engine ../kaihou-nlp-engine
cd ../kaihou-nlp-engine && ./install.sh
```

### 4️⃣  (Optional) Run an offline LLM with Ollama
```bash
ollama pull mistral          # or any other supported model
```

Now the console script `kaihou` is available inside the activated virtual environment.

---

## Quick Usage

```bash
# Interactive menu (repeat translations without exiting)
kaihou translate
```

```
=== Kaihou Interactive Menu ===
1) Translate
2) Exit
Select an option (1, 2) [1]: 1
Source language [en]: fr
Target language [fr]: en
Provide text directly or from a file? [text]: text
Text to translate: Bonjour le monde
Show full JSON output? [y/N]: n
Show debug info? [y/N]: n
```

### One‑shot (non‑interactive) commands
```bash
# Simple FR → EN translation
kaihou translate --text "Bonjour le monde" --from fr --to en --json

# Translate a file with a technical domain glossary
kaihou translate --file document.txt --from en --to fr --domain technical

# Force the multi‑LLM panel (run all configured LLMs)
kaihou translate --text "..." --from fr --to en --panel

# Machine‑readable output (JSON)
kaihou translate --text "..." --from fr --to en --json
```

#### Example JSON output
```json
{
  "translation": "Hello world",
  "validation": { "passed": true, "issues": [] },
  "used_panel": false,
  "llm_used": ["mistral_local"]
}
```

---

## Configuration

All runtime parameters live under `config/` and are YAML files.

| File | Purpose |
|------|---------|
| `models.yaml` | Defines LLM profiles (name, endpoint, connector class, strengths). |
| `pipeline.yaml` | Ordered list of pipeline steps, validation thresholds, adaptive‑mode rules. |
| `glossaries/*.yaml` | Term glossaries per domain (e.g., legal, medical, technical). |
| `plugins.yaml` | List of enabled plugin modules (LLM connectors, validators, decider, etc.). |

> **Tip:** When you add a new plugin, simply register its dotted path in `plugins.yaml`; the orchestrator will load it automatically.

For a complete technical reference see **`SPEC.md`** – it details data schemas, plugin interfaces, and the roadmap.

---

## Extending the Project

1. **Create a new plugin** (e.g., a different NLP engine or validator) by implementing the appropriate abstract base class in `kaihou_engine/plugins/base.py`.  
2. **Register the plugin** in `kaihou_engine/plugins/plugin_registry.py` (or directly in `config/plugins.yaml`).  
3. **Reference it** in `pipeline.yaml` or `plugins.yaml` using its module path, e.g.:
```yaml
- kaihou_engine.plugins.llm_connectors.my_custom_connector.MyConnector
```
No changes to the core pipeline code are required – the system is built for seamless plug‑and‑play.

---

## Roadmap

- **v1.x (FR ↔ EN)** – stable interactive CLI, multi‑LLM panel, adaptive mode, full validation.  
- **v2.0** – add additional language pairs (ES, DE, …).  
- **v2.1** – plug‑in support for remote LLM APIs (OpenAI, Anthropic).  
- **v3.0** – UI front‑end (Web) and integration with CI translation workflows.  

See **section 11 of `SPEC.md`** for a detailed breakdown of upcoming milestones.

---

## Publishing to PyPI

When you are ready to release a new version, create a tag and push it:
```bash
git tag v0.1.0   # bump the version appropriately
git push origin v0.1.0
```
A GitHub Actions workflow (`publish.yml`) will automatically build the distribution and upload it to PyPI using the secret `PYPI_API_TOKEN`. Make sure you have added this secret in **Settings → Secrets and variables → Actions** of the repository.

---

## Contributing

1. **Open an issue** first to discuss the change you intend to make.  
2. Fork the repository and create a branch off `develop`.  
3. Implement your feature or bug‑fix, adding tests as appropriate.  
4. Run the test suite locally: `pytest -q`. CI will also run these tests on every PR.  
5. Open a Pull Request targeting `develop`. Once CI passes and the PR is approved, Mergify will merge it and keep `main` up‑to‑date.

### CI status badge
[![CI](https://github.com/houtarou-d/kaihou-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/houtarou-d/kaihou-engine/actions/workflows/ci.yml)

---

## License

The project is released under the **MIT License** (see `LICENSE`). All third‑party dependencies are under permissive licenses (Apache 2.0, BSD, MPL) and are compatible with MIT.

---

### Thank you!
We hope `kaihou‑engine` helps you build trustworthy, domain‑aware translations. Feel free to reach out via GitHub issues for any questions, feature requests, or collaboration ideas. Happy translating! 🚀