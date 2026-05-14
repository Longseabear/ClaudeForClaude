# ClaudeForClaude

ClaudeForClaude (CLFC) is a Windows-first workspace helper for Claude Code.

The project is currently in the design and discovery phase. Its first goal is to understand Claude Code's local transcript system and build privacy-preserving tooling around it before adding heavier session-management features.

## Current Focus

- Analyze Claude Code transcript JSONL files under `~/.claude/projects`
- Build safe local summaries without storing prompt text, tool output, thinking text, or attachments
- Support Ollama-backed Claude Code routing through the Anthropic-compatible endpoint
- Define a CLFC command model that fits Claude Code instead of directly copying CodexForCodex

## Key Documents

- `AGENTS.md` is the implementation contract.
- `CLAUDE.md` tells Claude Code to use `AGENTS.md` as the source of truth.
- `docs/claude-conversation-system.md` records observed transcript structure and early product implications.
