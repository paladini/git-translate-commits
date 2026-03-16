# SPDX-FileCopyrightText: 2026 Fernando Paladini
# SPDX-License-Identifier: GPL-3.0-or-later

"""Main pipeline orchestrator that ties all modules together."""

from __future__ import annotations

import time
from datetime import datetime

from .git_reader import GitReader, GitReaderError
from .language_detector import detect_language, needs_translation, is_neutral_message
from .models import Config, RewriteReport
from .reporter import (
    console,
    print_confirmation_prompt,
    print_dry_run_report,
    print_execution_report,
)
from .rewriter import GitRewriter
from .translator_base import BaseTranslator


class PipelineError(Exception):
    pass


def _create_translator(config: Config) -> BaseTranslator:
    """Factory: create the appropriate translator based on config.engine."""
    if config.engine == "llm":
        from .translator import LLMTranslator

        return LLMTranslator(
            target_lang=config.lang,
            provider=config.provider,
            model=config.model,
            api_key=config.api_key,
            api_base_url=config.api_base_url,
            preserve_conventional=config.preserve_conventional,
            batch_size=config.batch_size,
            verbose=config.verbose,
        )
    else:
        from .translator_local import LocalTranslator

        return LocalTranslator(
            target_lang=config.lang,
            preserve_conventional=config.preserve_conventional,
            batch_size=config.batch_size,
            verbose=config.verbose,
        )


def run(config: Config) -> RewriteReport:
    """Execute the full translation pipeline."""

    # --- 1. Initialize git reader ---
    try:
        reader = GitReader(config.repo_path)
    except GitReaderError as e:
        raise PipelineError(str(e)) from e

    # --- 2. Validate repository state ---
    if reader.has_uncommitted_changes() and not config.dry_run:
        raise PipelineError(
            "Repository has uncommitted changes. "
            "Please commit or stash them before rewriting."
        )

    # --- 3. Determine branches ---
    if config.all_branches:
        branches = reader.get_all_local_branches()
    elif config.branches:
        branches = config.branches
    else:
        branches = [reader.get_current_branch()]

    if config.verbose:
        console.print(f"  Branches to process: {', '.join(branches)}")

    # --- 4. Read commits ---
    commits = reader.get_commits(
        branches=branches,
        author=config.author,
        since=config.since,
        until=config.until,
    )

    if not commits:
        console.print("[yellow]No commits found matching the criteria.[/yellow]")
        return RewriteReport(
            target_language=config.lang,
            branches_processed=branches,
            total_commits_scanned=0,
            already_in_target_language=0,
            translated_count=0,
            skipped_neutral=0,
        )

    if config.verbose:
        console.print(f"  Found {len(commits)} commits to analyze")

    # --- 5. Detect languages and determine what needs translation ---
    detected_languages: list[str | None] = []
    needs_translation_flags: list[bool] = []
    neutral_count = 0
    already_target_count = 0

    for commit in commits:
        msg = commit.full_message
        if is_neutral_message(msg):
            detected_languages.append(None)
            needs_translation_flags.append(False)
            neutral_count += 1
        else:
            lang = detect_language(msg)
            detected_languages.append(lang)
            needs_it = needs_translation(
                msg, config.lang, config.skip_already_translated
            )
            needs_translation_flags.append(needs_it)
            if not needs_it:
                already_target_count += 1

    to_translate_count = sum(needs_translation_flags)

    # --- 6. Build initial report ---
    translator = _create_translator(config)

    messages_to_translate = [
        commits[i].full_message
        for i in range(len(commits))
        if needs_translation_flags[i]
    ]
    estimated_tokens = translator.estimate_tokens(messages_to_translate)

    report = RewriteReport(
        target_language=config.lang,
        branches_processed=branches,
        total_commits_scanned=len(commits),
        already_in_target_language=already_target_count,
        translated_count=to_translate_count,
        skipped_neutral=neutral_count,
        estimated_tokens=estimated_tokens,
    )

    # --- 7. Dry-run: translate a sample for preview, then show report and exit ---
    if config.dry_run:
        if to_translate_count > 0:
            sample_size = min(to_translate_count, 10)
            sample_msgs = messages_to_translate[:sample_size]
            try:
                sample_translations = translator.translate_batch(sample_msgs)
                sample_idx = 0
                for i, commit in enumerate(commits):
                    if needs_translation_flags[i] and sample_idx < sample_size:
                        from .models import TranslationResult

                        report.translations.append(
                            TranslationResult(
                                original_hash=commit.hash,
                                original_message=commit.full_message,
                                translated_message=sample_translations[sample_idx],
                                detected_language=detected_languages[i] or "unknown",
                                was_translated=True,
                            )
                        )
                        sample_idx += 1
            except Exception as e:
                console.print(f"[red]Warning: Could not generate sample translations: {e}[/red]")

        report.estimated_tokens = estimated_tokens
        print_dry_run_report(report)
        return report

    # --- 8. No translations needed ---
    if to_translate_count == 0:
        console.print("[green]✔ All commits are already in the target language. Nothing to do.[/green]")
        return report

    # --- 9. Create backup ---
    if config.backup:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_name = f"backup/pre-rewrite-{timestamp}"
        try:
            reader.create_backup_branch(backup_name)
            report.backup_branch = backup_name
        except GitReaderError as e:
            raise PipelineError(f"Failed to create backup: {e}") from e

    # --- 10. Confirm with user ---
    if not config.force:
        report.backup_branch = report.backup_branch
        if not print_confirmation_prompt(report):
            console.print("[yellow]Aborted by user.[/yellow]")
            return report

    # --- 11. Translate all messages ---
    start_time = time.time()

    if config.verbose:
        console.print(f"  Translating {to_translate_count} messages in batches of {config.batch_size}...")

    translations = translator.translate_commits(
        commits, needs_translation_flags, detected_languages
    )
    report.translations = translations
    report.estimated_tokens = translator.total_tokens_used or estimated_tokens

    elapsed = time.time() - start_time
    report.elapsed_seconds = elapsed

    # --- 12. Apply rewrites ---
    if config.verbose:
        console.print("  Rewriting commit history...")

    rewriter = GitRewriter(config.repo_path, verbose=config.verbose)
    rewriter.rewrite(translations)

    # --- 13. Write log ---
    log_path = rewriter.write_log(translations)
    if config.verbose:
        console.print(f"  Log written to: {log_path}")

    # --- 14. Print report ---
    print_execution_report(report)

    return report
