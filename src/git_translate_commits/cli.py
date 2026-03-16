# SPDX-FileCopyrightText: 2026 Fernando Paladini
# SPDX-License-Identifier: GPL-3.0-or-later

"""CLI interface using Typer."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv
from rich.console import Console

from . import __version__
from .models import Config
from .pipeline import PipelineError, run

load_dotenv()

app = typer.Typer(
    name="git-translate-commits",
    help="Translate git commit messages to a target language. Supports local (offline) and LLM-based translation.",
    no_args_is_help=True,
)

console = Console()


def version_callback(value: bool) -> None:
    if value:
        console.print(f"git-translate-commits v{__version__}")
        raise typer.Exit()


@app.command()
def main(
    lang: str = typer.Option(
        ...,
        "--lang",
        "-l",
        help="Target language code (e.g. en, pt-BR, es, fr, de, ja).",
        envvar="GIT_TRANSLATE_LANG",
    ),
    all_branches: bool = typer.Option(
        False,
        "--all-branches",
        help="Process all local branches.",
    ),
    branches: Optional[list[str]] = typer.Option(
        None,
        "--branch",
        "-b",
        help="Specific branch(es) to process. Can be repeated.",
    ),
    author: Optional[str] = typer.Option(
        None,
        "--author",
        help="Filter commits by author email.",
    ),
    since: Optional[str] = typer.Option(
        None,
        "--since",
        help="Only process commits after this date (e.g. 2024-01-01).",
    ),
    until: Optional[str] = typer.Option(
        None,
        "--until",
        help="Only process commits before this date.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Show what would be changed without modifying anything.",
    ),
    engine: str = typer.Option(
        "local",
        "--engine",
        "-e",
        help="Translation engine: 'local' (offline, Argos Translate) or 'llm' (API-based).",
        envvar="GIT_TRANSLATE_ENGINE",
    ),
    provider: str = typer.Option(
        "openai",
        "--provider",
        "-p",
        help="LLM provider — only used with --engine llm (openai, anthropic, openai-compatible).",
        envvar="GIT_TRANSLATE_PROVIDER",
    ),
    model: str = typer.Option(
        "gpt-4o-mini",
        "--model",
        "-m",
        help="LLM model to use.",
        envvar="GIT_TRANSLATE_MODEL",
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        help="API key for the LLM provider. Prefer env vars OPENAI_API_KEY or ANTHROPIC_API_KEY.",
    ),
    api_base_url: Optional[str] = typer.Option(
        None,
        "--api-base-url",
        help="Base URL for OpenAI-compatible providers.",
    ),
    batch_size: int = typer.Option(
        20,
        "--batch-size",
        help="Number of messages per LLM request.",
    ),
    skip_already_translated: bool = typer.Option(
        True,
        "--skip-already-translated/--no-skip-already-translated",
        help="Skip messages already in the target language.",
    ),
    backup: bool = typer.Option(
        True,
        "--backup/--no-backup",
        help="Create a backup branch before rewriting.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed logs.",
    ),
    preserve_conventional: bool = typer.Option(
        True,
        "--preserve-conventional/--no-preserve-conventional",
        help="Preserve Conventional Commit prefixes (feat:, fix:, etc.).",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation prompt.",
    ),
    repo_path: str = typer.Option(
        ".",
        "--repo",
        "-r",
        help="Path to the git repository.",
    ),
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Translate git commit messages to a target language."""
    config = Config(
        lang=lang,
        engine=engine,
        all_branches=all_branches,
        branches=branches or [],
        author=author,
        since=since,
        until=until,
        dry_run=dry_run,
        provider=provider,
        model=model,
        api_key=api_key,
        api_base_url=api_base_url,
        batch_size=batch_size,
        skip_already_translated=skip_already_translated,
        backup=backup,
        verbose=verbose,
        preserve_conventional=preserve_conventional,
        force=force,
        repo_path=repo_path,
    )

    try:
        run(config)
    except PipelineError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user.[/yellow]")
        raise typer.Exit(code=130)


if __name__ == "__main__":
    app()
