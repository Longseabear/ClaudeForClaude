# ClaudeForClaude

ClaudeForClaude (CLFC) is a Windows-first workspace helper for Claude Code.

The project is currently in the design and discovery phase. Its first goal is to understand Claude Code's local transcript system and build privacy-preserving tooling around it before adding heavier session-management features.

## Installation

The PyPI package name is `claude-for-claude`.
The installed command is `clfc`.

Current install status:

- Installable now from GitHub or from a locally built wheel.
- Installable from PyPI after the first `claude-for-claude` release is uploaded with `twine`.

Install the current GitHub version:

```powershell
py -m pip install --upgrade "git+https://github.com/Longseabear/ClaudeForClaude.git"
clfc --help
clfc doctor
```

Install from PyPI after release:

```powershell
py -m pip install --upgrade claude-for-claude
clfc --help
clfc doctor
```

Install from a local checkout:

```powershell
git clone https://github.com/Longseabear/ClaudeForClaude.git
cd ClaudeForClaude
py -m pip install -e .
clfc doctor
```

The repository also includes `.\clfc.cmd` for development without installing:

```powershell
.\clfc.cmd doctor
```

See `docs/installation.md` for pipx, PATH troubleshooting, first-run setup, and uninstall instructions.

## Current Focus

- Analyze Claude Code transcript JSONL files under `~/.claude/projects`
- Build safe local summaries without storing prompt text, tool output, thinking text, or attachments
- Support Ollama-backed Claude Code routing through the Anthropic-compatible endpoint
- Define a CLFC command model that fits Claude Code instead of directly copying CodexForCodex

## Current Commands

```powershell
clfc doctor
clfc init
clfc interactive
clfc resume <session-id-or-prefix>
clfc fork <session-id-or-prefix>
clfc checkout <session-id-or-prefix>
clfc current
clfc memory status
clfc scan
clfc index
clfc list
clfc open
clfc name <session-id-or-prefix> <display-name>
clfc inspect <session-id-or-prefix>
clfc settings show
```

## Quick Start With `clfc`

Run these commands from the project workspace you want ClaudeForClaude to manage.

Check local readiness:

```powershell
clfc doctor
```

Initialize workspace metadata:

```powershell
clfc init
```

Index Claude Code transcripts for the current workspace:

```powershell
clfc index
```

List indexed sessions:

```powershell
clfc list
```

Open the numbered session picker:

```powershell
clfc open
```

Launch Claude Code interactively with CLFC defaults:

```powershell
clfc interactive
```

Resume an indexed Claude Code session from `list`:

```powershell
clfc index
clfc list
clfc resume 35ebc4da
```

Pick an indexed session from a numbered menu:

```powershell
clfc open
clfc open --select 1 --action checkout
clfc open --select 1 --action resume --dry-run
```

Check out a session as the active workspace session, then resume it without an argument:

```powershell
clfc init
clfc checkout 35ebc4da
clfc current
clfc resume
```

Give a session a CLFC-owned display name:

```powershell
clfc name 35ebc4da main
clfc resume main
clfc name main --clear
```

Fork an indexed session into a new Claude Code conversation:

```powershell
clfc resume 35ebc4da --fork
clfc fork 35ebc4da
clfc fork
```

Temporarily bypass Claude Code permission checks for one interactive launch:

```powershell
clfc interactive --dangerously-skip-permissions
```

Persist that behavior as a CLFC launcher default:

```powershell
clfc settings set dangerously-skip-permissions on
```

The same launcher flags work with `resume`:

```powershell
clfc resume 35ebc4da --dangerously-skip-permissions
```

Manage session-local `CLAUDE.md` behavior:

```powershell
clfc memory status
clfc memory mode sync
clfc memory init
clfc memory clone C:\path\to\CLAUDE.md
clfc memory clear
```

In `sync` mode, `resume` and `fork` run Claude from a per-session runtime workspace under `%USERPROFILE%\.clfc\...`, copy the nearest project `CLAUDE.md` into that runtime workspace, and add the real project directory with `--add-dir`.

This default is intentionally stored in CLFC's own settings file under `%LOCALAPPDATA%\clfc\settings.json`, not in Claude Code's global settings.

`scan`, `index`, `list`, and `inspect` are intentionally redacted. They summarize record types, block types, tool names, errors, models, and token usage without printing prompt text, tool output, thinking text, or attachment content.

## Development

Run tests with:

```powershell
python -m unittest discover -v
```

Build and validate the package locally:

```powershell
python -m build
python -m twine check dist/*
```

See `docs/publishing.md` for the full PyPI release checklist.

## Key Documents

- `AGENTS.md` is the implementation contract.
- `CLAUDE.md` tells Claude Code to use `AGENTS.md` as the source of truth.
- `docs/installation.md` covers user installation and first-run setup.
- `docs/publishing.md` covers PyPI/TestPyPI release flow.
- `docs/claude-conversation-system.md` records observed transcript structure and early product implications.
