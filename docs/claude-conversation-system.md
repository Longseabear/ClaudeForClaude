# Claude Code Conversation System Notes

Observed on Windows with Claude Code `2.1.141` and Ollama Anthropic-compatible routing.

These notes intentionally describe transcript structure without copying prompt text, tool output, or assistant content.

## Data roots

Claude Code stores project transcripts under:

```text
%USERPROFILE%\.claude\projects\<encoded-cwd>\<session-id>.jsonl
```

When `CLAUDE_CONFIG_DIR` is set, use that directory instead of `%USERPROFILE%\.claude`.

The observed project directory for:

```text
C:\Users\leap1\Documents\ClaudeForClaude
```

is:

```text
C--Users-leap1-Documents-ClaudeForClaude
```

Do not rely on reversing this directory name. The transcript records carry the authoritative `cwd`.

Claude also keeps a global app state file at:

```text
%USERPROFILE%\.claude.json
```

The observed keys there are app/cache/migration state, not the durable conversation log.

## Transcript model

Each session is one JSONL file. It is an append-oriented event log with a linked-list/tree shape.

Common top-level fields:

- `type`
- `sessionId`
- `timestamp`
- `uuid`
- `parentUuid`
- `cwd`
- `version`
- `message`
- `gitBranch`
- `permissionMode`
- `entrypoint`
- `userType`
- `isSidechain`

Common record types:

- `queue-operation`
- `user`
- `assistant`
- `attachment`
- `last-prompt`

There is no Codex-style single first-line `session_meta` record. Metadata is repeated on message-like records, and the active leaf is tracked by `last-prompt`.

## Turn shape

A simple first prompt produced:

```text
queue-operation(enqueue)
queue-operation(dequeue)
user
attachment
assistant
assistant
last-prompt
```

The first `attachment` was an initial `skill_listing` attachment. It contained a list of available skills and should be treated as sensitive transcript content for indexing purposes.

A resumed second prompt appended to the same file:

```text
queue-operation(enqueue)
queue-operation(dequeue)
user
assistant
assistant
last-prompt
```

The new user record had `parentUuid` set to the previous assistant leaf. The new `last-prompt.leafUuid` pointed to the latest assistant record.

## Message content

User prompt records may store content as a plain string:

```text
message.role = user
message.content = string
```

Assistant records store content as blocks:

```text
message.role = assistant
message.content = [
  { type = thinking, ... },
  { type = text, ... }
]
```

With the Ollama-backed test model, thinking blocks and text blocks were sometimes split into separate assistant records. CLFC should not assume one assistant record per turn.

Assistant usage metadata appears under `message.usage` and may include:

- `input_tokens`
- `output_tokens`
- `cache_creation`
- `cache_creation_input_tokens`
- `cache_read_input_tokens`
- `service_tier`
- `speed`
- `server_tool_use`
- `iterations`

This makes token/usage summaries a strong early feature.

## Tool calls

A tool-using turn produced:

```text
user(string prompt)
attachment(skill_listing)
assistant(thinking)
assistant(tool_use)
user(tool_result)
assistant(text)
last-prompt
```

The assistant `tool_use` block shape:

```text
type, id, name, input
```

For a shell call, the tool name was:

```text
Bash
```

The observed input keys were:

```text
command, description, run_in_background
```

The matching user `tool_result` block shape:

```text
type, tool_use_id, content, is_error
```

The `tool_result.tool_use_id` matched the assistant `tool_use.id`.

CLFC should index tool names, error flags, and byte/line counts, but not raw commands or tool output by default. Raw command indexing can leak paths, secrets, or file contents.

## Fork behavior

Running Claude Code with `--resume <source-session> --fork-session` created a new transcript file with a fresh `sessionId`.

Observed behavior:

- old conversation records were copied into the new file
- historical `uuid` and `parentUuid` values were preserved
- copied records had the new `sessionId`
- the source file was not used as the ongoing log for the fork
- the fork appended the new prompt and response after the copied leaf
- historical `last-prompt` records were not preserved as separate turn markers; the fork had a final `last-prompt`

This means clone/worker support should prefer native `--fork-session` over manual transcript copying.

## Privacy rules

Treat transcripts as plaintext sensitive data.

Do not store these in CLFC's global index by default:

- full prompts
- queue-operation `content`
- `lastPrompt`
- assistant text
- thinking text
- attachment content
- tool inputs
- tool output

Safe default index fields:

- `sessionId`
- `transcript_path`
- `cwd`
- `project_key`
- `created_at`
- `updated_at`
- `version`
- `gitBranch`
- `permissionMode`
- record counts by `type`
- message counts by role
- content block counts by block type
- tool names
- tool error counts
- aggregate token usage
- short content hashes for deduplication
- optional redacted preview only when explicitly enabled

## Implications for CLFC

CodexForCodex is rollout-first. CLFC should be transcript-analytics-first.

The first useful slice should be:

1. `clfc scan`
   Parse Claude transcripts safely and print a local summary without writing an index.

2. `clfc doctor`
   Verify `claude`, Ollama routing, config roots, transcript roots, and model availability.

3. `clfc index`
   Persist a privacy-preserving transcript index.

4. `clfc list`
   Show sessions by workspace with status, last activity, model, tool count, and token usage.

5. `clfc inspect <session>`
   Show a redacted event timeline and parent/leaf graph.

This order learns Claude's real local model before adding heavier session management like checkout, clone, templates, or workers.
