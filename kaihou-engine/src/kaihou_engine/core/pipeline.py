"""Pipeline implementation for Kaihou Engine.

The pipeline loosely follows the high‑level flow described in
``kaihou_spec.md`` (section 7).  For the initial version we implement a
single‑LLM (draft) path with optional validation plugins.  The design is
modular so additional steps (multi‑LLM panel, adaptive mode, correction
loop) can be added later.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Tuple

import click
from pydantic import ValidationError

from ..core.schemas import SourceAnalysis, TranslationRequest, LLMDraft, ValidationReport, TerminologyContext

from ..plugins.base import LLMConnectorPlugin

from ..plugins.plugin_registry import load_plugins

# ---------------------------------------------------------------------------
# Helper to run the external ``kaihou-nlp-engine`` CLI and obtain a parsed model.
# ---------------------------------------------------------------------------

def _run_nlp_engine(input_text: str, lang: str) -> SourceAnalysis:
    """Execute ``nlp_engine.cli`` as a subprocess and parse its ``--json`` output.

    ``input_text`` is passed via ``--input -`` (stdin) because the CLI expects a
    file path; we therefore create a temporary file.
    """
    # Write temporary input file
    tmp_path = Path.cwd() / ".tmp_input.txt"
    tmp_path.write_text(input_text, encoding="utf-8")
    cmd = [
        "python",
        "-m",
        "nlp_engine.cli",
        "analyze",
        str(tmp_path),
        "-l",
        lang,
        "--json",
    ]
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
    except Exception as exc:
        # Fallback stub if external nlp engine unavailable
        from .schemas import SourceAnalysis, Token
        stub_token = Token(
            text="",
            lemma="",
            pos="",
            tag="",
            morph={},
            dep="",
            head_index=0,
            index=0,
        )
        return SourceAnalysis(
            raw_text=input_text,
            language=lang,
            tokens=[stub_token],
            entities=[],
            sentences=[input_text],
        )
    finally:
        # Clean up temporary file regardless of success/failure
        try:
            tmp_path.unlink()
        except Exception:
            pass
    try:
        return SourceAnalysis.model_validate_json(completed.stdout)
    except ValidationError as exc:
        raise PipelineError(f"Invalid JSON from nlp engine: {exc}") from exc


# ---------------------------------------------------------------------------
# Core pipeline function used by the CLI.
# ---------------------------------------------------------------------------

def run_translation_pipeline(
    *,
    source_text: str,
    source_lang: str,
    target_lang: str,
    config_path: Path | None = None,
) -> Tuple[Dict[str, Any], List[ValidationReport]]:
    """Run the full translation pipeline and return a JSON‑serialisable dict.

    The returned dict mirrors the ``TranslationRequest`` plus the final
    translation and a flag indicating whether a multi‑LLM panel was used.
    ``validation_reports`` contains the individual validator results.
    """
    # 1️⃣ Load configuration (currently only used for future extension).
    # For now we ignore it – the default behaviour is hard‑coded.
    if config_path:
        # In a full implementation we would parse pipeline steps here.
        pass

    # 2️⃣ Load plugins (registry returns instances keyed by import path).
    plugins = load_plugins()

    # 3️⃣ NLP analysis (source)
    source_analysis = _run_nlp_engine(source_text, source_lang)

    # 4️⃣ Terminology context – use the glossary_substitutor plugin as a query
    #    placeholder (it actually performs substitution after translation).
    glossary_plugin = plugins.get("kaihou_engine.plugins.glossary_substitutor")
    terminology_context = glossary_plugin.process({}) if glossary_plugin else {"terminology_hits": [], "dictionary_entries": []}
    # Convert the plain dict into the expected ``TerminologyContext`` model lazily.
    from ..core.schemas import TerminologyContext

    terminology = TerminologyContext.model_validate(terminology_context)

    # 5️⃣ Build the translation request model
    request = TranslationRequest(
        source_text=source_text,
        source_lang=source_lang,
        target_lang=target_lang,
        analysis=source_analysis,
        terminology=terminology,
        instructions=[],
    )

    # Store debug info (source analysis and request) for optional output
    debug_info = {
        "source_analysis": source_analysis.model_dump(),
        "request": request.model_dump(),
    }

    # 6️⃣ Choose LLM connectors
    # Gather all LLMConnectorPlugin instances
    llm_connectors = [p for p in plugins.values() if isinstance(p, LLMConnectorPlugin)]
    if not llm_connectors:
        raise PipelineError("No LLM connector plugin found for translation")

    # Determine whether to run panel mode (multiple LLMs) from config
    # For now we read a simple flag from the optional pipeline config file
    use_panel = False
    if config_path and config_path.is_file():
        from ..core.config import load_yaml_file
        cfg = load_yaml_file(config_path)
        use_panel = cfg.get("use_panel", False)

    if use_panel:
        # Run all draft LLMs concurrently
        async def _run_all():
            return await asyncio.gather(*[c.translate(request) for c in llm_connectors])
        drafts = asyncio.run(_run_all())
        # Try to find a decider plugin (role "decider")
        decider = next((p for p in llm_connectors if getattr(p, "role", "") == "decider"), None)
        if decider:
            decision = asyncio.run(decider.decide(request, drafts))
            final_translation = decision.final_translation
            llm_used = [d.llm_id for d in drafts]
            used_panel = True
        else:
            # Fallback: pick first draft
            final_translation = drafts[0].translated_text
            llm_used = [drafts[0].llm_id]
            used_panel = True
    else:
        # Single draft – pick the first connector
        draft_connector = llm_connectors[0]
        async def _translate_one():
            return await draft_connector.translate(request)
        draft = asyncio.run(_translate_one())
        final_translation = draft.translated_text
        llm_used = [draft.llm_id]
        used_panel = False

    # 8️⃣ Assemble final output dict (including raw draft info)
    output: Dict[str, Any] = {
        "source_text": source_text,
        "source_lang": source_lang,
        "target_lang": target_lang,
        "translation": final_translation,
        "llm_used": llm_used,
        "used_panel": used_panel,
        "debug": debug_info,
    }


    # 9️⃣ Apply glossary substitution after translation (if plugin exists).
    if glossary_plugin:
        processed = glossary_plugin.process({"translation": final_translation}, target_language=target_lang)
        output["translation"] = processed.get("translation", output["translation"])  # type: ignore

    # 🔟 Validation – run each validator plugin and collect reports.
    validation_reports: List[ValidationReport] = []
    for plugin in plugins.values():
        from ..plugins.base import ValidatorPlugin
        if isinstance(plugin, ValidatorPlugin):
            report = plugin.validate(request, _run_nlp_engine(output["translation"], target_lang))
            validation_reports.append(report)

    output["validation"] = {
        "passed": all(r.passed for r in validation_reports),
        "issues": [issue.dict() for r in validation_reports for issue in r.issues],
    }
    return output, validation_reports


__all__ = ["run_translation_pipeline"]
