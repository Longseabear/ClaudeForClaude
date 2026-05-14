from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path

from clfc.core.index import ResolveError, resolve_record, set_display_name, write_index
from clfc.core.paths import iter_transcript_files, workspace_transcripts
from clfc.core.transcript import summarize_transcript


def run(args: Namespace) -> int:
    if args.clear and args.display_name is not None:
        print("Use either a display name or --clear, not both.", file=sys.stderr)
        return 2

    workspace = Path(args.workspace).expanduser().resolve() if args.workspace else Path.cwd()
    if args.refresh:
        files = iter_transcript_files() if args.all else workspace_transcripts(workspace)
        write_index([summarize_transcript(path) for path in files])

    try:
        if args.clear:
            record = set_display_name(args.session, None, workspace=workspace, all_workspaces=args.all)
        elif args.display_name is not None:
            record = set_display_name(args.session, args.display_name, workspace=workspace, all_workspaces=args.all)
        else:
            record = resolve_record(args.session, workspace=workspace, all_workspaces=args.all)
    except ResolveError as error:
        print(str(error), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(record, indent=2, ensure_ascii=False))
        return 0

    session_id = str(record.get("session_id") or "")
    display_name = str(record.get("display_name") or "")
    if args.clear:
        print(f"Cleared display name for {session_id}.")
    elif args.display_name is not None:
        print(f"Named {session_id}: {display_name}")
    else:
        print(f"{session_id}: {display_name or '<unnamed>'}")
    return 0
