from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from clfc.core.index import read_all_records, read_workspace_records, write_index
from clfc.core.paths import iter_transcript_files, workspace_transcripts
from clfc.core.transcript import summarize_transcript
from clfc.utils.output import format_table


def run(args: Namespace) -> int:
    workspace = Path(args.workspace).expanduser().resolve() if args.workspace else Path.cwd()
    if args.refresh:
        files = iter_transcript_files() if args.all else workspace_transcripts(workspace)
        write_index([summarize_transcript(path) for path in files])

    records = read_all_records() if args.all else read_workspace_records(workspace)

    if args.json:
        print(json.dumps(records, indent=2, ensure_ascii=False))
        return 0

    scope = "all indexed workspaces" if args.all else str(workspace)
    print(f"Indexed sessions: {scope}")
    if not records:
        print("No indexed Claude Code sessions found. Run `clfc index` first.")
        return 0

    rows = []
    for record in records[: max(args.limit, 0)]:
        usage = record.get("usage") if isinstance(record.get("usage"), dict) else {}
        rows.append(
            [
                _short(str(record.get("session_id", ""))),
                str(record.get("display_name") or ""),
                _short(str(record.get("workspace_hash", "")), 6) if args.all else "",
                record.get("updated_at") or "",
                _models(record.get("model_counts")),
                _count(record, "role_counts", "user"),
                _count(record, "role_counts", "assistant"),
                _tool_count(record),
                record.get("tool_error_count", 0),
                usage.get("input_tokens", 0),
                usage.get("output_tokens", 0),
            ]
        )

    headers = ["session", "name"]
    if args.all:
        headers.append("ws")
    headers.extend(["updated", "models", "user", "asst", "tools", "errs", "in_tok", "out_tok"])
    print(format_table(headers, _trim_workspace_column(rows, args.all)))
    if len(records) > args.limit:
        print(f"... {len(records) - args.limit} more hidden by --limit")
    return 0


def _trim_workspace_column(rows: list[list[object]], include_workspace: bool) -> list[list[object]]:
    if include_workspace:
        return rows
    return [[row[0], row[1], *row[3:]] for row in rows]


def _short(value: str, length: int = 8) -> str:
    return value[:length]


def _models(model_counts: object) -> str:
    if not isinstance(model_counts, dict):
        return ""
    return ",".join(str(model) for model in model_counts.keys())


def _count(record: dict[str, object], group: str, key: str) -> int:
    counts = record.get(group)
    if not isinstance(counts, dict):
        return 0
    value = counts.get(key, 0)
    return int(value) if isinstance(value, int) else 0


def _tool_count(record: dict[str, object]) -> int:
    counts = record.get("tool_counts")
    if not isinstance(counts, dict):
        return 0
    return sum(value for value in counts.values() if isinstance(value, int))
