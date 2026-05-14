from __future__ import annotations

import sys
from argparse import Namespace
from pathlib import Path
from typing import Callable

from clfc.cli.commands.launch import launch_record
from clfc.core.index import read_all_records, read_workspace_records, set_display_name, write_index
from clfc.core.paths import iter_transcript_files, workspace_transcripts
from clfc.core.transcript import summarize_transcript
from clfc.core.workspace import WorkspaceError, active_session_id, set_active_session
from clfc.utils.output import format_table

Action = str
Prompt = Callable[[str], str]

ACTION_ALIASES = {
    "": "resume",
    "r": "resume",
    "resume": "resume",
    "f": "fork",
    "fork": "fork",
    "i": "inspect",
    "inspect": "inspect",
    "c": "checkout",
    "checkout": "checkout",
    "n": "name",
    "name": "name",
    "q": "quit",
    "quit": "quit",
}


def run(args: Namespace) -> int:
    workspace = Path(args.workspace).expanduser().resolve() if args.workspace else Path.cwd()
    if args.refresh:
        files = iter_transcript_files() if args.all else workspace_transcripts(workspace)
        write_index([summarize_transcript(path) for path in files])

    records = read_all_records() if args.all else read_workspace_records(workspace)
    visible_records = records[: max(args.limit, 0)]
    active_id = _active_id(workspace)

    if not records:
        print("No indexed Claude Code sessions found. Run `clfc index` first.")
        return 0
    if not visible_records:
        print("No sessions are visible with the current --limit value.", file=sys.stderr)
        return 2

    print(_format_picker_table(visible_records, active_id=active_id, include_workspace=args.all))
    if len(records) > len(visible_records):
        print(f"... {len(records) - len(visible_records)} more hidden by --limit")

    record, status = _select_record(visible_records, args.select, prompt=input)
    if record is None:
        return status

    action, status = _select_action(args.action, prompt=input)
    if action is None:
        return status
    if action == "quit":
        return 0

    return _run_action(action, record, workspace, args)


def _run_action(action: Action, record: dict[str, object], workspace: Path, args: Namespace) -> int:
    if action == "resume":
        return _launch(record, workspace, args, fork_session=False)
    if action == "fork":
        return _launch(record, workspace, args, fork_session=True)
    if action == "checkout":
        try:
            set_active_session(workspace, record)
        except WorkspaceError as error:
            print(str(error), file=sys.stderr)
            return 1
        print(f"Checked out {_session_id(record)} ({_display_name(record) or '<unnamed>'})")
        return 0
    if action == "name":
        display_name = _display_name_arg(args)
        if display_name is None:
            return 2
        try:
            named = set_display_name(_session_id(record), display_name, workspace=workspace, all_workspaces=args.all)
        except ValueError as error:
            print(str(error), file=sys.stderr)
            return 1
        print(f"Named {_session_id(named)}: {_display_name(named) or '<unnamed>'}")
        return 0
    if action == "inspect":
        return _inspect_record(record)

    print(f"Unsupported action: {action}", file=sys.stderr)
    return 2


def _launch(record: dict[str, object], workspace: Path, args: Namespace, *, fork_session: bool) -> int:
    return launch_record(
        record,
        workspace,
        model=args.model,
        effort=args.effort,
        permission_mode=args.permission_mode,
        dangerously_skip_permissions=args.dangerously_skip_permissions,
        allow_dangerously_skip_permissions=args.allow_dangerously_skip_permissions,
        fork_session=fork_session,
        name=args.launch_name,
        bare=args.bare,
        add_dirs=args.add_dir or [],
        dry_run=args.dry_run,
        checkout_new=args.checkout_new if fork_session else False,
        display_name=args.display_name if fork_session else None,
    )


def _inspect_record(record: dict[str, object]) -> int:
    path = Path(str(record.get("path") or "")).expanduser()
    if not path.exists():
        print(f"Transcript path is missing: {path}", file=sys.stderr)
        return 1

    summary = summarize_transcript(path, include_events=True)
    print(f"Session: {summary.session_id}")
    print(f"Path: {summary.path}")
    print(f"CWD: {summary.cwd or '<unknown>'}")
    print(f"Updated: {summary.updated_at or '<unknown>'}")
    print(f"Models: {', '.join(summary.model_counts.keys()) or '<none>'}")
    print(f"Usage: input={summary.usage.input_tokens} output={summary.usage.output_tokens}")
    print()

    rows = [
        [
            event.index,
            event.record_type or "",
            event.role or "",
            event.operation or "",
            ",".join(event.block_types),
            ",".join(event.tool_names),
            "yes" if event.tool_error else "",
            _short(event.uuid),
        ]
        for event in summary.events
    ]
    print(format_table(["#", "type", "role", "op", "blocks", "tools", "err", "uuid"], rows))
    return 0


def _format_picker_table(
    records: list[dict[str, object]],
    *,
    active_id: str | None,
    include_workspace: bool,
) -> str:
    rows: list[list[object]] = []
    for index, record in enumerate(records, start=1):
        usage = record.get("usage") if isinstance(record.get("usage"), dict) else {}
        rows.append(
            [
                index,
                _short(_session_id(record)),
                "*" if _session_id(record) == active_id else "",
                _display_name(record),
                _short(str(record.get("workspace_hash") or ""), 6) if include_workspace else "",
                record.get("updated_at") or "",
                _models(record.get("model_counts")),
                _tool_count(record),
                record.get("tool_error_count", 0),
                usage.get("input_tokens", 0),
                usage.get("output_tokens", 0),
            ]
        )

    headers = ["#", "session", "active", "name"]
    if include_workspace:
        headers.append("ws")
    headers.extend(["updated", "models", "tools", "errs", "in_tok", "out_tok"])
    return format_table(headers, _trim_workspace_column(rows, include_workspace))


def _select_record(
    records: list[dict[str, object]],
    selected: int | None,
    *,
    prompt: Prompt,
) -> tuple[dict[str, object] | None, int]:
    if selected is not None:
        if selected < 1 or selected > len(records):
            print(f"--select must be between 1 and {len(records)}.", file=sys.stderr)
            return None, 2
        return records[selected - 1], 0

    if not sys.stdin.isatty():
        print("Use --select in non-interactive shells.", file=sys.stderr)
        return None, 2

    while True:
        raw = prompt(f"Select session [1-{len(records)}, q]: ").strip()
        if raw.lower() in {"q", "quit"}:
            return None, 0
        try:
            value = int(raw)
        except ValueError:
            print("Enter a session number or q.")
            continue
        if 1 <= value <= len(records):
            return records[value - 1], 0
        print(f"Enter a number between 1 and {len(records)}.")


def _select_action(action: Action | None, *, prompt: Prompt) -> tuple[Action | None, int]:
    if action is not None:
        normalized = ACTION_ALIASES.get(action.lower())
        if normalized is None:
            print(f"Unsupported action: {action}", file=sys.stderr)
            return None, 2
        return normalized, 0

    if not sys.stdin.isatty():
        print("Use --action in non-interactive shells.", file=sys.stderr)
        return None, 2

    while True:
        raw = prompt("Action [r]esume/[f]ork/[i]nspect/[c]heckout/[n]ame/[q]uit (resume): ").strip().lower()
        normalized = ACTION_ALIASES.get(raw)
        if normalized is not None:
            return normalized, 0
        print("Choose resume, fork, inspect, checkout, name, or quit.")


def _display_name_arg(args: Namespace) -> str | None:
    display_name = args.display_name
    if display_name is not None:
        return display_name

    if not sys.stdin.isatty():
        print("Use --display-name with `--action name` in non-interactive shells.", file=sys.stderr)
        return None

    raw = input("Display name: ").strip()
    if not raw:
        print("Display name cannot be empty.", file=sys.stderr)
        return None
    return raw


def _trim_workspace_column(rows: list[list[object]], include_workspace: bool) -> list[list[object]]:
    if include_workspace:
        return rows
    return [[row[0], row[1], row[2], row[3], *row[5:]] for row in rows]


def _models(model_counts: object) -> str:
    if not isinstance(model_counts, dict):
        return ""
    return ",".join(str(model) for model in model_counts.keys())


def _tool_count(record: dict[str, object]) -> int:
    counts = record.get("tool_counts")
    if not isinstance(counts, dict):
        return 0
    return sum(value for value in counts.values() if isinstance(value, int))


def _active_id(workspace: Path) -> str | None:
    try:
        return active_session_id(workspace)
    except WorkspaceError:
        return None


def _session_id(record: dict[str, object]) -> str:
    return str(record.get("session_id") or "")


def _display_name(record: dict[str, object]) -> str:
    return str(record.get("display_name") or "")


def _short(value: str | None, length: int = 8) -> str:
    if not value:
        return ""
    return value[:length]
