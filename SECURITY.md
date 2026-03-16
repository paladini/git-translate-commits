# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 1.x     | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do NOT open a public issue.**
2. Email **fernando@paladini.dev** with details of the vulnerability.
3. Include steps to reproduce, if possible.
4. Allow reasonable time for a fix before public disclosure.

You will receive an acknowledgment within 48 hours, and a detailed response within 7 days indicating the next steps.

## Security Considerations

- **API keys**: When using `--engine llm`, API keys are handled via environment variables or CLI flags. They are never logged or written to disk.
- **Repository access**: This tool operates on local git repositories. It does not make network requests except when using LLM translation or downloading Argos Translate language packs.
- **History rewriting**: This tool modifies git history. Always use `--backup` (enabled by default) and verify changes with `--dry-run` first.
