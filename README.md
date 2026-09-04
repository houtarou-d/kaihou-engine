# Kaihou NLP Engine (spaCy)

A lightweight Python library that performs **pure linguistic analysis** using spaCy. It extracts tokens, lemmas, universal POS tags, morphological features, dependency relations and named entities, and returns the result as a structured `SourceAnalysis` Pydantic model. An optional Rich‑based display (`--json` flag disabled) provides a human‑readable tree. This engine is designed to be consumed by the higher‑level **`kaihou-engine`** orchestrator.

## Features

- Tokenization, lemmatization, universal POS (UPOS), morphology, head index and dependency label.
- Named Entity Recognition (entity text, label, character offsets).
- Structured output via the `SourceAnalysis` Pydantic model.
- Optional `--json` CLI flag for machine‑readable output.
- Human‑friendly Rich tree rendering (`nlp_engine.display.render_analysis`).
- Supports English, French and other spaCy models (Spanish still available). No Spanish‑only translation layer.
- Simple CLI for analysis and language listing.

## Installation

```bash
# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download required spaCy models (e.g., English and French)
python -m spacy download en_core_web_sm
python -m spacy download fr_core_news_sm
# Optional: other languages such as Spanish
# python -m spacy download es_core_news_sm
```

## Usage

```bash
# Analyse a sentence (default language is English)
python -m nlp_engine.cli analyze "The children are playing in the park"

# Specify a different language (French example)
python -m nlp_engine.cli analyze "Les enfants jouent dans le parc" -l fr

# Get machine‑readable JSON output
python -m nlp_engine.cli analyze "Hello world" --json

# List supported language codes
python -m nlp_engine.cli list‑langs
```

The JSON output matches the `SourceAnalysis` schema and can be imported directly by **`kaihou-engine`**.

## Adding a new language

1. Open `nlp_engine/analyzer.py`.
2. Extend the `model_map` dictionary inside `SpaCyAnalyzer.__init__` with a new entry, e.g.:
   ```python
   model_map = {"en": "en_core_web_sm", "fr": "fr_core_news_sm", "es": "es_core_news_sm"}
   ```
3. Install the model: `python -m spacy download <model_name>`.
4. The CLI automatically accepts the new `--lang` code.

## License

MIT – feel free to adapt and share!
