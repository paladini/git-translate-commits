# SPDX-FileCopyrightText: 2026 Fernando Paladini
# SPDX-License-Identifier: GPL-3.0-or-later

"""Module for formatting and displaying output reports."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table

from .models import RewriteReport, TranslationResult


console = Console()

MAX_SAMPLE_TRANSLATIONS = 10


def print_dry_run_report(report: RewriteReport) -> None:
    """Print a formatted dry-run report showing what would be changed."""
    console.print()
    console.print("[bold cyan]📋 git-translate-commits — Dry Run[/bold cyan]")
    console.print()
    console.print(f"  Target language: [bold]{report.target_language}[/bold]")
    console.print(f"  Branches: [bold]{', '.join(report.branches_processed)}[/bold]")
    console.print(f"  Total commits scanned: [bold]{report.total_commits_scanned}[/bold]")
    console.print(
        f"  Already in target language: [green]{report.already_in_target_language}[/green]"
    )
    console.print(f"  Neutral/skipped: [dim]{report.skipped_neutral}[/dim]")
    console.print(f"  To be translated: [bold yellow]{report.translated_count}[/bold yellow]")
    console.print()

    translated = [t for t in report.translations if t.was_translated]
    if translated:
        console.print("[bold]Sample translations:[/bold]")
        for t in translated[:MAX_SAMPLE_TRANSLATIONS]:
            short_hash = t.original_hash[:7]
            orig = _truncate(t.original_message.split("\n")[0], 50)
            trans = _truncate(t.translated_message.split("\n")[0], 50)
            console.print(f'  [dim]{short_hash}[/dim] "{orig}" → "{trans}"')

        remaining = len(translated) - MAX_SAMPLE_TRANSLATIONS
        if remaining > 0:
            console.print(f"  [dim]... ({remaining} more)[/dim]")
        console.print()

    if report.estimated_tokens > 0:
        cost = report.estimated_cost_usd
        console.print(
            f"  Estimated API cost: [bold]~${cost:.4f}[/bold] "
            f"(~{report.estimated_tokens:,} tokens)"
        )
    else:
        console.print("  Engine: [bold green]local (offline, no cost)[/bold green]")
    console.print()
    console.print("[dim]Run without --dry-run to apply changes.[/dim]")
    console.print()


def print_execution_report(report: RewriteReport) -> None:
    """Print a formatted execution report after rewriting."""
    console.print()
    console.print("[bold green]🔄 git-translate-commits[/bold green]")
    console.print()

    if report.backup_branch:
        console.print(f"  [green]✔[/green] Backup created: [bold]{report.backup_branch}[/bold]")

    console.print(
        f"  [green]✔[/green] Scanned {report.total_commits_scanned} commits "
        f"across {len(report.branches_processed)} branch(es)"
    )
    console.print(
        f"  [green]✔[/green] Detected {report.translated_count} commits needing translation"
    )

    num_batches = max(1, report.translated_count // 20 + 1)
    console.print(
        f"  [green]✔[/green] Translated {report.translated_count} messages "
        f"in {num_batches} batch(es) ({report.elapsed_seconds:.1f}s)"
    )
    console.print(
        f"  [green]✔[/green] Done! {report.translated_count} commits translated "
        f"to {report.target_language}."
    )
    console.print()
    console.print("[bold]📊 Summary:[/bold]")
    console.print(f"   Commits processed: {report.total_commits_scanned}")
    console.print(f"   Translated: [bold]{report.translated_count}[/bold]")
    console.print(f"   Skipped (already in target): {report.already_in_target_language}")
    console.print(f"   Skipped (neutral): {report.skipped_neutral}")
    if report.estimated_tokens > 0:
        console.print(f"   API tokens used: ~{report.estimated_tokens:,}")
        console.print(f"   Estimated cost: ${report.estimated_cost_usd:.4f}")
    else:
        console.print("   Engine: local (offline, no cost)")
    console.print()

    if report.backup_branch:
        console.print(
            "[bold yellow]⚠️  Commit hashes have changed.[/bold yellow] "
            "If this repo is shared, coordinate with your team before force-pushing."
        )
        console.print(f"   Backup branch: [bold]{report.backup_branch}[/bold]")
        console.print()


def print_confirmation_prompt(report: RewriteReport) -> bool:
    """Show a summary and ask for user confirmation. Returns True if confirmed."""
    console.print()
    console.print("[bold yellow]⚠️  About to rewrite commit history[/bold yellow]")
    console.print()
    console.print(f"  Commits to translate: [bold]{report.translated_count}[/bold]")
    if report.estimated_tokens > 0:
        console.print(f"  Estimated cost: [bold]~${report.estimated_cost_usd:.4f}[/bold]")
    else:
        console.print("  Engine: [bold green]local (offline, no cost)[/bold green]")
    console.print(f"  Backup branch: [bold]{report.backup_branch or 'disabled'}[/bold]")
    console.print()
    console.print("[dim]This will change commit hashes. This operation cannot be undone without the backup.[/dim]")
    console.print()

    try:
        answer = console.input("[bold]Proceed? [y/N]: [/bold]").strip().lower()
        return answer in ("y", "yes")
    except (KeyboardInterrupt, EOFError):
        return False


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."
