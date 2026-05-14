# Architecture

ClaudeForClaude starts with a read-only transcript observability layer.

## Layers

```text
clfc.cli
  commands and argument parsing

clfc.core.paths
  Claude config root, projects root, workspace transcript discovery

clfc.core.transcript
  JSONL event parsing and safe summarization

clfc.core.settings
  CLFC launcher defaults stored under the CLFC data root

clfc.core.runner
  Thin Claude Code interactive launcher command builder

clfc.core.summaries
  Dataclasses for transcript, event, and usage summaries

clfc.utils
  JSONL, hashing, and console output helpers
```

## Safety Boundary

The parser may read transcript content to understand record shapes, but command output and future indexes must not include raw:

- prompt text
- assistant text
- thinking text
- attachment content
- tool input
- tool output

The safe default surface is metadata:

- session ids
- transcript paths
- cwd
- timestamps
- record counts
- role counts
- content block counts
- tool names
- tool error counts
- model names
- aggregate token usage

## Near-Term Direction

The first production slice is:

1. `doctor`
2. `scan`
3. `inspect`
4. privacy-preserving local index
5. fast `list` from that index
6. `resume` from indexed session prefixes
7. CLFC-owned display names for stable human selection
8. local `.clfc/workspace.json` active checkout
9. native Claude Code fork launcher for indexed or active sessions

Session mutation features such as checkout, templates, and workers should come after the transcript model is stable.

Interactive launching is intentionally thin. CLFC does not reimplement Claude Code; it builds a `claude` command with saved defaults and lets Claude Code own the interactive experience.
