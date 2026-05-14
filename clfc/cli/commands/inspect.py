from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path

from clfc.core.index import ResolveError, resolve_record
from clfc.core.paths import iter_transcript_files, workspace_transcripts
from clfc.core.transcript import summarize_transcript
from clfc.utils.output import format_table


def run(args: Namespace) -> int:
    path = _resolve_session(args)
    if path is None:
        return 1

    summary = summarize_transcript(path, include_events=True)
    if args.json:
        print(json.dumps(summary.to_dict(include_events=True), indent=2, ensure_ascii=False))
        return 0

    print(f"Session: {summary.session_id}")
    print(f"Path: {summary.path}")
    print(f"CWD: {summary.cwd or '<unknown>'}")
    print(f"Updated: {summary.updated_at or '<unknown>'}")
    print(f"Leaf: {_short(summary.leaf_uuid)}")
    print(f"Models: {', '.join(summary.model_counts.keys()) or '<none>'}")
    print(f"Usage: input={summary.usage.input_tokens} output={summary.usage.output_tokens}")
    print()

    rows = []
    for event in summary.events:
        rows.append(
            [
                event.index,
                event.record_type or "",
                event.role or "",
                event.operation or "",
                ",".join(event.block_types),
                ",".join(event.tool_names),
                "yes" if event.tool_error else "",
                _short(event.uuid),
                _short(event.parent_uuid),
            ]
        )
    print(format_table(["#", "type", "role", "op", "blocks", "tools", "err", "uuid", "parent"], rows))
    return 0


def _resolve_session(args: Namespace) -> Path | None:
    raw = args.session
    candidate = Path(raw).expanduser()
    if candidate.exists():
        return candidate.resolve()

    workspace = Path(args.workspace).expanduser().resolve() if args.workspace else Path.cwd()
    try:
        record = resolve_record(raw, workspace=workspace, all_workspaces=args.all)
    except ResolveError as error:
        if not str(error).startswith("No indexed session matched"):
            print(str(error), file=sys.stderr)
            return None
    else:
        indexed_path = Path(str(record.get("path") or "")).expanduser()
        if indexed_path.exists():
            return indexed_path.resolve()

    files = iter_transcript_files() if args.all else workspace_transcripts(workspace)
    matches = [path for path in files if path.stem == raw or path.stem.startswith(raw)]
    if not matches:
        print(f"No transcript matched {raw!r}.", file=sys.stderr)
        return None
    if len(matches) > 1:
        print(f"Ambiguous session prefix {raw!r}; matched {len(matches)} transcripts.", file=sys.stderr)
        for path in matches[:10]:
            print(f"  {path.stem}", file=sys.stderr)
        return None
    return matches[0]


def _short(value: str | None, length: int = 8) -> str:
    if not value:
        return ""
    return value[:length]
