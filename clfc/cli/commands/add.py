from __future__ import annotations

import json
import sys
import uuid
from argparse import Namespace
from pathlib import Path

from clfc.core.index import ResolveError, create_manual_record, resolve_record, set_display_name, write_index
from clfc.core.paths import iter_transcript_files, workspace_transcripts
from clfc.core.transcript import summarize_transcript
from clfc.core.workspace import set_active_session


def run(args: Namespace) -> int:
    workspace = Path(args.workspace).expanduser().resolve() if args.workspace else Path.cwd()
    if args.refresh:
        files = iter_transcript_files() if args.all else workspace_transcripts(workspace)
        write_index([summarize_transcript(path) for path in files])

    try:
        record, created = _add_record(args, workspace)
        if args.checkout:
            set_active_session(workspace, record)
    except ResolveError as error:
        print(str(error), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps({"created": created, "checked_out": bool(args.checkout), "session": record}, indent=2, ensure_ascii=False))
        return 0

    verb = "Added" if created else "Named"
    print(f"{verb} {record.get('session_id')}: {record.get('display_name')}")
    if created and record.get("launch_mode") == "session-id":
        print("  first launch will use `claude --session-id`")
    if args.checkout:
        print("  checked out")
    return 0


def _add_record(args: Namespace, workspace: Path) -> tuple[dict[str, object], bool]:
    if args.session:
        try:
            record = resolve_record(args.session, workspace=workspace, all_workspaces=args.all)
        except ResolveError as error:
            if not str(error).startswith("No indexed session matched"):
                raise
            _validate_uuid(args.session)
            return (
                create_manual_record(
                    args.display_name,
                    workspace,
                    session_id=args.session,
                    launch_mode="resume",
                ),
                True,
            )
        return set_display_name(str(record.get("session_id") or ""), args.display_name, workspace=workspace, all_workspaces=args.all), False

    return create_manual_record(args.display_name, workspace, launch_mode="session-id"), True


def _validate_uuid(value: str) -> None:
    try:
        uuid.UUID(value)
    except ValueError as error:
        raise ResolveError(
            f"No indexed session matched {value!r}. Use a full UUID to add an unindexed session."
        ) from error
