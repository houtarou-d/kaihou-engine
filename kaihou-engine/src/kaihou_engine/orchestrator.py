"""Kaihou Engine command‑line interface.

Provides a ``translate`` sub‑command that runs the full translation
pipeline (analysis, optional terminology substitution, LLM draft, and
validation).  The CLI mirrors the usage described in ``kaihou_spec.md``
(section 10).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Tuple, List

import click
try:
    from rich import print as rprint
except ImportError:
    # Fallback to built‑in print if Rich is unavailable.
    def rprint(*args, **kwargs):
        print(*args, **kwargs)
from .core.pipeline import run_translation_pipeline











def _interactive_loop() -> None:
    """Run an interactive menu for repeated translations."""
    while True:
        click.echo("\n=== Kaihou Interactive Menu ===")
        click.echo("1) Translate")
        click.echo("2) Exit")
        choice = click.prompt(
            "Select an option",
            type=click.Choice(["1", "2"], case_sensitive=False),
            default="1",
        )
        if choice == "2":
            click.echo("Goodbye!")
            break

        # Gather parameters
        src = click.prompt("Source language", default="en")
        tgt = click.prompt("Target language", default="fr")
        input_mode = click.prompt(
            "Provide text directly or from a file?",
            type=click.Choice(["text", "file"], case_sensitive=False),
            default="text",
        )
        if input_mode == "file":
            path = click.prompt(
                "Path to file",
                type=click.Path(exists=True, path_type=Path),
            )
            source_text = Path(path).read_text(encoding="utf-8")
        else:
            source_text = click.prompt("Text to translate")

        as_json = click.confirm("Show full JSON output?", default=False)
        debug = click.confirm("Show debug info?", default=False)

        try:
            result, _ = run_translation_pipeline(
                source_text=source_text,
                source_lang=src,
                target_lang=tgt,
                config_path=None,
            )
        except Exception as exc:
            rprint(f"[bold red]Pipeline error:[/bold red] {exc}")
            continue

        if as_json or debug:
            click.echo(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            rprint("[bold green]Translation result:[/bold green]")
            rprint(result.get("translation", ""))
            rprint("\n[bold cyan]Validation summary:[/bold cyan]")
            validation = result.get("validation", {})
            passed = validation.get("passed", False)
            rprint(f"Passed: {'✅' if passed else '❌'}")
            if not passed:
                for issue in validation.get("issues", []):
                    rprint(f"- {issue.get('type')}: {issue.get('detail')} ({issue.get('severity')})")
            if debug:
                rprint("\n[bold magenta]Debug info:[/bold magenta]")
                rprint(json.dumps(result.get("debug", {}), ensure_ascii=False, indent=2))




@click.group()
def cli() -> None:
    """Top‑level command group for Kaihou Engine."""


@cli.command()
@click.option("--text", "text_input", type=str, help="Plain text to translate (mutually exclusive with --file).")
@click.option("--file", "file_path", type=click.Path(exists=True, path_type=Path), help="Path to a file containing the source text.")
@click.option("--from", "src_lang", required=False, help="Source language code (e.g., fr, en).")
@click.option("--to", "tgt_lang", required=False, help="Target language code (e.g., en, fr).")
@click.option("--config", "config_path", type=click.Path(exists=True, path_type=Path), default=None, help="Custom pipeline configuration YAML file.")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output the full result as JSON.")
@click.option("--debug", "debug", is_flag=True, default=False, help="Show full pipeline debug info (analysis, request, etc.)")







def translate(
    text_input: str | None,
    file_path: Path | None,
    src_lang: str | None,
    tgt_lang: str | None,
    config_path: Path | None,
    as_json: bool,
    debug: bool,
) -> None:
    """Translate *text* from *src_lang* to *tgt_lang* using the Kaihou pipeline."""
    # ----- Interactive mode detection -----
    # If any of the core arguments are missing, fall back to an interactive menu.
    if not (text_input or file_path) or not src_lang or not tgt_lang:
        _interactive_loop()
        return

    # ----- Non‑interactive path (original behavior) -----
    if not text_input and not file_path:
        raise click.UsageError("Either --text or --file must be provided.")
    if text_input and file_path:
        raise click.UsageError("Provide only one of --text or --file.")

    if file_path:
        source_text = file_path.read_text(encoding="utf-8")
    else:
        source_text = text_input  # type: ignore[arg-type]

    try:
        result, _ = run_translation_pipeline(
            source_text=source_text,
            source_lang=src_lang,
            target_lang=tgt_lang,
            config_path=config_path,
        )
    except Exception as exc:
        rprint(f"[bold red]Pipeline error:[/bold red] {exc}")
        raise click.Abort()

    if as_json or debug:
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        rprint("[bold green]Translation result:[/bold green]")
        rprint(result.get("translation", ""))
        rprint("\n[bold cyan]Validation summary:[/bold cyan]")
        validation = result.get("validation", {})
        passed = validation.get("passed", False)
        rprint(f"Passed: {'✅' if passed else '❌'}")
        if not passed:
            for issue in validation.get("issues", []):
                rprint(f"- {issue.get('type')}: {issue.get('detail')} ({issue.get('severity')})")
        if debug:
            rprint("\n[bold magenta]Debug info:[/bold magenta]")
            rprint(json.dumps(result.get("debug", {}), ensure_ascii=False, indent=2))





def main() -> None:
    cli()


if __name__ == "__main__":
    main()
