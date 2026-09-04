# Kaihou Engine

**Kaihou Engine** is the orchestration layer that coordinates the various language‑specific analysis tools (e.g., `kaihou-nlp-engine`) and provides a unified pipeline for text processing, translation, and enrichment.

## Project Layout
```
 kaihou-engine/
 ├─ .github/
 │   ├─ stale.yml          # Stale bot configuration
 │   └─ mergify.yml        # Mergify bot configuration
 ├─ config/
 │   ├─ models.yaml        # spaCy / language model definitions
 │   ├─ pipeline.yaml      # Ordered pipeline steps
 │   ├─ glossaries.yaml    # Term glossaries for translation
 │   └─ plugins.yaml       # Optional plugin registration
 ├─ src/
 │   └─ kaihou_engine/
 │       ├─ __init__.py
 │       └─ orchestrator.py # Core orchestrator implementation
 ├─ pyproject.toml          # Build / dependencies
 ├─ .gitignore
 └─ README.md              # (this file)
```

## Getting Started

```bash
# Clone the repository
git clone https://github.com/houtarou-d/kaihou-engine.git
cd kaihou-engine

# Create a virtual environment and install the package in editable mode
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

The package installs a console script named `kaihou`.

## Usage

### Interactive mode
```bash
kaihou translate
```
You will see a menu allowing you to translate or exit.

### One‑shot translation (non‑interactive)
```bash
kaihou translate --text "Bonjour le monde" --from fr --to en --json
```
Additional flags:
- `--debug` – show detailed pipeline debug information.
- `--config <path>` – use a custom pipeline configuration YAML file.



## Configuration
All configuration files are in the `config/` directory and are written in **YAML**. They are loaded by the orchestrator at runtime.

- **models.yaml** – defines which spaCy models to load for each language.
- **pipeline.yaml** – lists the processing steps (e.g., `tokenize`, `analyze`, `translate`).
- **glossaries.yaml** – optional term glossaries used by translation plugins.
- **plugins.yaml** – registration of optional plugin modules.

## Running the Orchestrator
```bash
python -m kaihou_engine.orchestrator \
    --input "path/to/input.txt" \
    --output "path/to/output.json" \
    --config config/pipeline.yaml
```
The orchestrator will:
1. Load the requested spaCy language models.
2. Call the `kaihou-nlp-engine` CLI as a subprocess to obtain a `SourceAnalysis` JSON.
3. Apply any configured plugins (glossary substitution, post‑processing, etc.).
4. Write the final, enriched JSON to the output file.

## Development Branch
All new features should be developed on the `develop` branch. The `main` branch reflects a stable, release‑ready state.

## Bot Configuration
- **Stale Bot** – automatically marks inactive pull requests and issues as stale. See `.github/stale.yml`.
- **Mergify** – automatically merges pull requests that satisfy the required status checks and review approvals. See `.github/mergify.yml`.

## Contributing
1. Create a feature branch from `develop`.
2. Write tests and ensure they pass.
3. Open a Pull Request targeting `develop`.
4. Once approved, Mergify will merge it and keep `main` up‑to‑date.

## License
This project is licensed under the MIT License.
