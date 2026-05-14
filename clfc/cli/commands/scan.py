from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from clfc.core.paths import iter_transcript_files, workspace_transcripts
from clfc.core.transcript import summarize_transcript
from clfc.utils.output import format_table


def run(args: Namespace) -> int:
    workspace = Path(args.workspace).expanduser().resolve() if args.workspace else Path.cwd()
    files = iter_transcript_files() if args.all else workspace_transcripts(workspace)
    summaries = [summarize_transcript(path) for path in files]
    summaries.sort(key=lambda item: item.updated_at or "", reverse=True)

    if args.json:
        print(json.dumps([summary.to_dict() for summary in summaries], indent=2, ensure_ascii=False))
        return 0

    scope = "all workspaces" if args.all else str(workspace)
    print(f"Transcript scan: {scope}")
    if not summaries:
        print("No Claude Code transcripts found.")
        return 0

    rows = []
    for summary in summaries[: max(args.limit, 0)]:
        rows.append(
            [
                _short(summary.session_id),
                summary.updated_at or "",
                _models(summary.model_counts),
                summary.user_messages,
                summary.assistant_messages,
                summary.tool_calls,
                summary.tool_error_count,
                summary.usage.input_tokens,
                summary.usage.output_tokens,
            ]
        )
    print(
        format_table(
            ["session", "updated", "models", "user", "asst", "tools", "errs", "in_tok", "out_tok"],
            rows,
        )
    )
    if len(summaries) > args.limit:
        print(f"... {len(summaries) - args.limit} more hidden by --limit")
    return 0


def _short(value: str, length: int = 8) -> str:
    return value[:length]


def _models(model_counts: dict[str, int]) -> str:
    if not model_counts:
        return ""
    return ",".join(model_counts.keys())
